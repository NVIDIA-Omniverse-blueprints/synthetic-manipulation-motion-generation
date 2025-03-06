import asyncio
import os
import io
import enum
import json
from typing import Any, Dict, List, Tuple
import zipfile
from dataclasses import dataclass
import logging

import aiohttp


FUNCTION_URL = "https://ai.api.nvidia.com/v1/cosmos/nvidia/cosmos-transfer"

class NVCF_URL(str, enum.Enum):
    PROD = "https://api.nvcf.nvidia.com/v2/nvcf"

    def __str__(self) -> str:
        return self.value


@dataclass
class Result:
    response_text: str
    output: Any
    status_code: int


def _format_request(
    command: str,
    token: str,
    asset_names: List[str] = [],
) -> Tuple[dict[str, Any], dict[str, str]]:
    """Format input parameters for an NVCF function to produce request body and and request headers.

    Args:
        command (str): Command to run.
        token (str): JWT token.
        asset_names (typing.List[str]): List of asset names.

    Returns:
        typing.Tuple[dict[str, typing.Any], dict[str, str]]: Request body and headers dictionaries.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "NVCF-POLL-SECONDS": "3600",
    }
    # TODO: assumes assets are pre-processed into asset IDs

    # process any inputs to include as assets to upload
    if len(asset_names) > 0:
        headers["NVCF-INPUT-ASSET-REFERENCES"] = ",".join(asset_names)

    request = {
        # "requestHeader": request_header,
        "requestBody": {"inputs": [{"name": "command", "shape": [1], "datatype": "BYTES", "data": [command]}]},
    }

    request["requestBody"]["inputs"] += [
                    {
                        "name": f"image_assetId_{i}",
                        "shape": [1],
                        "datatype": "BYTES",
                        "data": [asset],
                    }
                    for i, asset in enumerate(asset_names)
                ]
    return request["requestBody"], headers


def _generate_command(api: str, params: Dict[str, Any]) -> str:
    # return "probe"
    return f"{api} " + " ".join([f"--{k}={v}" for k, v in params.items()])


async def _create_asset_async(
    session: aiohttp.ClientSession,
    token: str,
    asset_name: str,
    content_type: str,
    nvcf_url: str = NVCF_URL.PROD,
) -> aiohttp.ClientResponse:
    """Create an NVCF asset named `asset_name` of the desired content type.

    Args:
        session (aiohttp.ClientSession): Client session.
        token (str): JWT authorization token.
        asset_name (str): Name to give the asset.
        content_type (str): MIME type of content stored in the asset. (ex: "image/jpeg")
        nvcf_url (str, optional): URL for NVCF calls. Defaults to NVCF_URL.PROD.

    Returns:
        aiohttp.ClientResponse: Result from POST call to create the asset.
    """
    # note: TTL is 1 hour for assets
    url = f"\n{nvcf_url}/assets"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {"contentType": content_type, "description": asset_name}
    async with session.post(url, headers=headers, json=data) as response:
        await response.read()
        return response


async def _upload_asset_async(
    session: aiohttp.ClientSession,
    asset_url: str,
    asset_name: str,
    content_type: str,
    asset_data: Any,
) -> aiohttp.ClientResponse:
    """Upload asset data of a content type to a named asset with associated URL.

    Args:
        session (aiohttp.ClientSession): Client session.
        asset_url (str): URL for the NVCF asset. Returned in response to asset creation.
        asset_name (str): Name given to the asset when created.
        content_type (str): MIME type of content stored in the asset. (ex: "image/jpeg")
        asset_data (Any): Raw data to upload.

    Returns:
        aiohttp.ClientResponse: Result from POST call to create the asset.
    """
    headers = {
        "Content-Type": content_type,
        "x-amz-meta-nvcf-asset-description": asset_name,
    }
    async with session.put(asset_url, data=asset_data, headers=headers) as response:
        await response.read()
        return response


async def _prepare_local_asset_async(
    session: aiohttp.ClientSession,
    token: str,
    asset_name: str,
    filepath: str,
    nvcf_url: str = NVCF_URL.PROD,
) -> str:
    """Helper to create and then upload asset data with an asset name. Provides the generated asset ID as output.
    Assumes "application/octet-stream" data to upload encoded image bytes.

    Args:
        session (aiohttp.ClientSession): Client session.
        token (str): JWT authorization token.
        asset_name (str): Name given to the asset when created.
        filepath (str): Path to the file to upload.
        nvcf_url (str, optional): URL for NVCF calls. Defaults to NVCF_URL.PROD.

    Returns:
        str: ID of the created asset.
    """
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError(f"{filepath} not found")

    with open(filepath, "rb") as file:
        file_binary = file.read()

    asset_result = await _create_asset_async(
        session,
        token,
        asset_name,
        content_type="binary/octet-stream",
        nvcf_url=nvcf_url,
    )
    result_json = await asset_result.json()
    asset_url = result_json["uploadUrl"]
    asset_id = result_json["assetId"]
    result = await _upload_asset_async(
        session,
        asset_url,
        asset_name,
        content_type="binary/octet-stream",
        asset_data=file_binary,
    )
    if result.status != 200:
        response_text = await result.text()
        print(f"Image upload failed with status code {result.status}: {response_text}.")
        return
    return asset_id


async def _poll_response_async(
    session: aiohttp.ClientSession,
    response: aiohttp.ClientResponse,
    token: str,
    nvcf_url: str = NVCF_URL.PROD,
    initial_delay: float = 0.001,
    max_attempts: int = 10,
    max_backoff: float = 32.0,
) -> aiohttp.ClientResponse:
    """Poll a pending NVCF request (status 202) until it is no longer pending.
    Uses exponential backoff for retries.

    Args:
        session (aiohttp.ClientSession): Client session.
        response (aiohttp.ClientResponse): NVCF request response.
        token (str): JWT token.
        nvcf_url (str, optional): URL for NVCF calls. Defaults to NVCF_URL.PROD.
        initial_delay (float, optional): Initial delay between retries in seconds. Defaults to 0.001.
        max_attempts (int, optional): Maximum number of retry attempts. Defaults to 10.
        max_backoff (float, optional): Maximum delay between retries in seconds. Defaults to 32.0.

    Returns:
        aiohttp.ClientResponse: Response from the request that is no longer pending.

    Raises:
        TimeoutError: If max attempts reached without successful response.
        aiohttp.ClientError: If request fails with network or HTTP error.
    """
    attempt = 0
    delay = initial_delay

    while response.status == 202 and attempt < max_attempts:
        try:
            json = await response.json()
            request_id = json["reqId"]
            url = f"{nvcf_url}/exec/status/{request_id}"

            async with session.get(url, headers={"Authorization": f"Bearer {token}"}) as response:
                await response.read()
                if response.status != 202:
                    break
                
                attempt += 1
                if attempt < max_attempts:
                    delay = min(delay * 2, max_backoff)  # Exponential backoff
                    logging.debug(f"Request pending, retrying in {delay}s (attempt {attempt}/{max_attempts})")
                    await asyncio.sleep(delay)
                
        except aiohttp.ClientError as e:
            logging.error(f"Network error during polling: {str(e)}")
            raise

    if attempt >= max_attempts:
        logging.error("Polling timed out after maximum attempts")
        raise TimeoutError("Maximum polling attempts reached")

    return response


async def process_response(response: aiohttp.ClientResponse) -> Dict:
    """Retrieve data from response
    
    Args:
        response (aiohttp.ClientResponse): NVCF request response.

    Returns:
        Dict: Parsed response data.

    Raises:
        ValueError: If response format is invalid or unsupported.
        json.JSONDecodeError: If JSON response is malformed.
    """
    try:
        if response.content_type == "application/json":
            response_text = await response.text()
            return json.loads(response_text)
        elif response.content_type == "application/zip":
            return await _unpack_zip_response_async(response)
        else:
            logging.error(f"Unsupported content type: {response.content_type}")
            raise ValueError(f"Unsupported content type: {response.content_type}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error processing response: {str(e)}")
        raise


async def _unpack_zip_response_async(response: aiohttp.ClientResponse) -> Dict:
    """Retrieve and unpack an API call response that provides a reference to output assets.
    NOTE: Assumes there is a single output provided in the zip file.

    Args:
        response (aiohttp.ClientResponse): Zipped NVCF request response.

    Returns:
        Dictionary loaded result from the response.
    """
    # large payload: response has "responseReference" with zipped data
    # async with session.get(response["responseReference"]) as zip_result:
    content = await response.read()

    zip_content = io.BytesIO(content)

    assert zipfile.is_zipfile(zip_content)

    # Extract the zip file
    output = {}
    with zipfile.ZipFile(zip_content) as zip_archive:
        zipped_files = zip_archive.namelist()

        for zipped_file in zipped_files:
            if zipped_file.endswith(".json"):
                output[os.path.basename(zipped_file)[:-5]] = json.loads(zip_archive.read(zipped_file))
            elif zipped_file.endswith(".png"):
                output["image"] = zip_archive.read(zipped_file)
            elif zipped_file.endswith(".mp4"):
                output["video"] = zip_archive.read(zipped_file)
    return output


async def api_call_async(
    token: str,
    params: Dict[str, Any],
    filepaths: List[str],
    nvcf_url: str = NVCF_URL.PROD,
) -> Any:
    """Single call to run an NVCF function end-to-end.

    Args:
        token (str): NGC API token.
        params (Dict[str, Any]): Dictionary of input parameters to the NVCF call.
        filepaths (List[str]): List of filepaths to upload as assets.
        nvcf_url (str, optional): URL for NVCF calls. Defaults to NVCF_URL.PROD.

    Returns:
        Any: Unzipped payload output from the NVCF call.
    """
    session_timeout = aiohttp.ClientTimeout(total=None,sock_connect=100,sock_read=600)
    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        asset_names = []
        for filepath in filepaths:
            asset_names.append(await _prepare_local_asset_async(
                session,
                token,
                asset_name=filepath,
                filepath=filepath,
                nvcf_url=nvcf_url,
            ))

        # post inference call
        command = _generate_command("vis_control", params)
        request, headers = _format_request(command, token=token, asset_names=asset_names)
        async with session.post(FUNCTION_URL, json=request, headers=headers) as response:
            response = await _poll_response_async(session, response, token=token, nvcf_url=nvcf_url)
            if response.status != 200:
                # TODO: handle 200 status but error in text. issue is errors are no longer raised
                return Result(
                    response_text=await response.text(),
                    output=None,
                    status_code=response.status,
                )

            # process zip file output
            try:
                output = await process_response(response)
                return Result(
                    response_text=output,
                    output=output,
                    status_code=response.status,
                )
            except aiohttp.ConnectionTimeoutError as e:
                return Result(
                    response_text="Connection Timeout",
                    output=None,
                    status_code=response.status,
                )
