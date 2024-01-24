from typing import List
from enforce_typing import enforce_types


@enforce_types
def get_pm2_deploy_template(name: str, run_command: List[str], private_key: str) -> str:
    run_command_str = " ".join(run_command)
    run_command_escaped = run_command_str.replace('"', '\\"')
    template = f"""module.exports = {{
  apps : [{{
    "name": "{name}",
    "script": "python {run_command_escaped}",
    "env": {{
      "PRIVATE_KEY": "{private_key}"
    }},
    "watch": false,
    "exec_mode": "fork",
    "restart_delay": 5000,
    "autorestart": true,
  }}]
}}"""
    return template
