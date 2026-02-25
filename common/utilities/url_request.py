import httpx


async def url_request(
    url: str = None,
    cookies: dict[str, str] | None = None,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """
    Use client provided or create a new client and make an async HTTP request (GET or POST)
    and safely return content or an error message.

    :param url: The URL to request.
    :param cookies: Optional cookies dictionary.
    :param method: "GET" (default) or "POST".
    :param payload: Data to send in POST body.
    :param headers: Optional request headers.
    :param client: Optional pre-configured httpx.AsyncClient.
    :return: {'response': content} or {'Error': message}.
    """
    # Reuse existing client if provided, otherwise create a new one
    owns_client = client is None

    if owns_client:
        client = httpx.AsyncClient(
            verify=False,
            cookies=cookies,
            timeout=httpx.Timeout(60.0),
        )

    else:
        # shared client → do NOT modify cookie jar if cookies is None
        if cookies:
            client.cookies.update(cookies)

    try:
        if method.upper() == "POST":
            response = await client.post(url, data=payload, headers=headers, )
        else:
            response = await client.get(url, headers=headers, )

        response.raise_for_status()
        return {"response": response.content}

    except httpx.HTTPStatusError as e:
        return {"Error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
    except httpx.RequestError as e:
        # return {"Error": f"Request error: {str(e)}"}
        return {
            "Error": repr(e),
            "Type": type(e).__name__
        }

    finally:
        if owns_client:
            await client.aclose()

