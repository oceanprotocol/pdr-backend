from enforce_typing import enforce_types

from pdr_backend.util.network_pp import NetworkPP


@enforce_types
def test_network_pp():
    d_my = {
        "address_file" : "my address.json",
        "rpc_url" : "my rpc url",
        "subgraph_url" : "my subgraph url",
        "stake_token" : "my 0x stake token",
        "owner_addrs" : "my 0x owner addrs",
    }
    d_another = {
        "address_file" : "another address.json",
        "rpc_url" : "another rpc url",
        "subgraph_url" : "another subgraph url",
        "stake_token" : "another 0x stake token",
        "owner_addrs" : "another 0x owner addrs",
    }
    d = {
        "my_network": d_my,
        "another network" : d_another, 
    }

    pp = NetworkPP("my_network", d)
    pp2 = NetworkPP("another network", d)
    
    # yaml properties
    assert pp.network == "my_network"
    assert pp.dn == d_my
    assert pp.address_file == "my address.json"
    assert pp.rpc_url == "my rpc url"
    assert pp.subgraph_url == "my subgraph url"
    assert pp.owner_addrs == "my 0x owner addrs"

    assert pp2.network == "another network"
    assert pp2.dn == d_another
    assert pp2.address_file == "another address.json"

    # str
    assert "NetworkPP=" in str(pp)
