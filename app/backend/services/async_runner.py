import asyncio
import streamlit as st


def run_async(coro, key: str = None, *args, **kwargs):
    """
    coro - name of async function (without () )
    Run an async coroutine in a synchronous context.
    Store result in session state if key is provided.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Always create the coroutine object first
    coro_obj = coro(*args, **kwargs)

    async def wrapper():
        """ Wrapper to run coroutine  """
        result = await coro_obj
        if key:
            st.session_state[key] = result
        return result

    if loop.is_running():
        asyncio.create_task(wrapper())
        return None
    else:
        return loop.run_until_complete(wrapper())
