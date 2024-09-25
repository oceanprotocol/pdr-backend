from typing import List, Optional, Tuple

import dash
from enforce_typing import enforce_types


@enforce_types
def toggle_modal_helper(
    ctx: dash._callback_context.CallbackContext,
    modal_id: str,
    is_open_input: bool,
    selected_rows: Optional[List],
) -> Tuple[bool, List[int]]:
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    modal_type = modal_id.split("_")[0]
    safe_trigger_ids = [f"{modal_type}_page_table", modal_id]

    if triggered_id not in safe_trigger_ids:
        return dash.no_update, dash.no_update

    if triggered_id == modal_id:
        if is_open_input:
            return dash.no_update, dash.no_update

        # Modal close button is clicked, clear the selection
        return False, []

    if selected_rows and not is_open_input:
        return True, dash.no_update

    # Clear the selection if modal is not opened
    return False, []
