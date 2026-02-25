import httpx
import xmltodict
import io
import gzip
import zipfile
import chardet
import re

from common.utilities.url_request import url_request


async def download_url(url: str, cookies: dict[str, str] | None = None,
                       client: httpx.AsyncClient | None = None) -> bytes | dict:
    """ Function to get the content of the specified URL """
    try:
        # Download the file
        if client is not None:
            response = await url_request(url, client=client)
        else:
            response = await url_request(url, cookies=cookies, )
        return response['response']

    except Exception as e:
        return {"error": str(e)}


async def extract_xml_bytes(file_bytes: bytes) -> bytes:
    """
    Detect whether file_bytes is gzip, zip, or plain XML,
    and return the extracted XML bytes.
    """
    # If structured data / str
    if isinstance(file_bytes, str):
        # Detect encoding
        detected = chardet.detect(file_bytes.encode())  # fallback
        encoding = detected['encoding'] or 'utf-8'
        print('encoding:', encoding)
        file_bytes = file_bytes.encode(encoding)

    # GZIP magic number
    if file_bytes[:2] == b"\x1f\x8b":
        return gzip.decompress(file_bytes)

    # ZIP magic number
    if file_bytes[:4] == b"PK\x03\x04":
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            # Pick the first XML file inside the ZIP
            for name in z.namelist():
                if name.lower().endswith(".xml"):
                    return z.read(name)
            raise ValueError("No XML file found inside ZIP archive")

    # Otherwise, assume it's already plain XML
    return file_bytes


def sanitize_xml(xml_bytes: bytes) -> str:
    """
    Sanitize malformed XML content before parsing.
    Fixes:
      - spaces in closing/opening tags
      - stray ampersands (&)
      - text beyond </Root>
      - UTF BOMs
    """
    # Detect encoding
    detected = chardet.detect(xml_bytes)
    encoding = detected.get('encoding', 'utf-8')
    text = xml_bytes.decode(encoding, errors='ignore')

    # Remove BOM if present
    text = text.replace("\ufeff", "")

    # Fix invalid tag spacing
    text = re.sub(r'<(\w+)\s+>', r'<\1>', text)
    text = re.sub(r'</(\w+)\s+>', r'</\1>', text)

    # Escape stray ampersands
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', text)

    # Truncate anything after </Root>
    match = re.search(r'</Root>', text)
    if match:
        text = text[:match.end()]

    return text


async def fix_missing_subchain(xml_bytes: bytes) -> bytes:
    """
    Insert missing </SubChain> before </SubChains> if it's missing.
    Returns bytes ready for xmltodict or ET parsing.
    """
    # Decode bytes (detect UTF BOM or fallback to utf-8)
    xml_text = xml_bytes.decode('utf-8-sig')  # removes BOM if present

    # Check if </SubChain> exists before </SubChains>
    if '</SubChain>' not in xml_text.split('</SubChains>')[0]:
        # Insert the missing closing tag
        xml_text = xml_text.replace('</SubChains>', '</SubChain></SubChains>')

    # Return as bytes
    return xml_text.encode('utf-8')


async def data_dict(url: str, cookies: dict[str, str] | None = None,
                    client: httpx.AsyncClient | None = None) -> dict:
    """ Function to extract data to dict from the specified URL file"""
    if client is not None:
        downloaded_content = await download_url(url=url, client=client)
    else:
        downloaded_content = await download_url(url=url, cookies=cookies, )
    xml_bytes = await extract_xml_bytes(downloaded_content)

    if 'hazihinam' in url.lower():
        xml_bytes = await fix_missing_subchain(xml_bytes)

    try:
        return xmltodict.parse(xml_bytes)
    except Exception as e:
        print("XML parsing failed:", e)
        raise
