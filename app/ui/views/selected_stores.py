import streamlit as st

from ui.elements.static import logo
from ui.utilities.general import remove_home_store_from_db


def make_data_for_editor(data: list[dict]):
    """ Make the data ready for insert into data_editor by adding delete column """
    return [{**d, 'delete': False, } for d in data]


def reorganize_data(edited_data: list[dict]):
    """ Reorganize data after edit by user """
    keys_to_remove = ["delete", ]
    # Remove keys and remove rows with delete=True
    stores = [
        {k: v for k, v in d.items() if k not in keys_to_remove}
        for d in edited_data
        if not d.get("delete", False)
    ]
    # Remove home store if removed from selected stores
    home_store_removed = remove_home_store_from_db(stores=stores)
    # Save updated stores data to session_state and indexedDB
    st.session_state.db.put(item_id='stores', value=stores)

    if home_store_removed:
        # Go to select new home store
        st.switch_page('ui/views/home_store.py')
    else:
        st.switch_page('ui/views/other_stores.py')


def render():
    """ Page to manage selected stores. Main function to render page """
    logo()
    st.divider()
    st.space()

    # Get selected stores
    data = st.session_state.db.get(item_id='stores')
    # Display selected stores
    if data:
        organized_data = make_data_for_editor(data.get('value'))
        edited_data = st.data_editor(
            data=organized_data, width='stretch',
            column_order=['chain_alias', 'store_name', 'delete'],
            column_config={'chain_alias': st.column_config.TextColumn(label='Chain', disabled=True),
                           'store_name': st.column_config.TextColumn(label='Store Name', disabled=True),
                           'chain_code': st.column_config.TextColumn(label='Chain Code'),
                           'store_code': st.column_config.TextColumn(label='Store'),
                           'delete': st.column_config.CheckboxColumn(label='Delete', width='small', )
                           }
        )
        # Update stores, go to home store selection if home store removed
        if st.button(label='Update',
                     icon=':material/refresh:',
                     icon_position='left',
                     width='stretch'):
            reorganize_data(edited_data)

        st.space()
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            # Back to stores selection
            if st.button(label='Back',
                         width='stretch',
                         icon=':material/west:',
                         icon_position='left'):
                st.switch_page('ui/views/other_stores.py')
        with col2:
            # Forward to items or shoppinglist
            if st.button(label='Next',
                         width='stretch',
                         icon=':material/east:',
                         icon_position='right'):
                if st.session_state.get('activity') == 'info':
                    st.switch_page('ui/views/items.py')
                if st.session_state.get('activity') == 'plan':
                    pass


if __name__ == "__main__":
    render()
