import dash

def toggle_modal_helper(
        ctx,
        selected_rows,
        is_open_input,
        safe_trigger_ids=None,
        modal_id=None,
    ):
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

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