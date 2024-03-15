// SPDX-License-Identifier: None
pragma solidity ^0.8.13;

import "./interfaces/IERC20.sol";
import "./interfaces/ITemplate3.sol";

contract Predictoor {
    bool public initialized;
    address public master;
    address public owner;
    address public oceanTokenAddr;

    /// @param owner_ EOA that os the owner of the system
    /// @param oceanTokenAddr_ address of the ocean token in the especific network
    /// @notice initializes the clone with required params
    function initialize(address owner_, address oceanTokenAddr_) external {
        require(initialized == false, "Already initialized");
        initialized = true;
        master = msg.sender;
        oceanTokenAddr = oceanTokenAddr_;
        owner = owner_;
    }

    /// @notice block unauthorized calls
    modifier onlyMaster() {
        require(msg.sender == master || msg.sender == owner, "Only owner or master can access");
        _;
    }

    ///@notice approve unlimmited ocean tokens to the feeds
    function approveOcean(address[] calldata feeds) public onlyMaster {
        IERC20 ocean = IERC20(oceanTokenAddr);
        uint256 n = feeds.length;
        for (uint256 i = 0; i < n; i++) {
            ocean.approve(feeds[i], (2 ** 256) - 1);
        }
    }

    ///@notice send predictions (up or Down) to each of the feeds
    function predict(
        bool[] calldata predictions,
        uint256[] calldata stakes,
        address[] calldata feeds,
        uint256 epoch_start
    ) external onlyMaster {
        uint256 n = predictions.length;
        for (uint256 i = 0; i < n; i++) {
            ITemplate3 feedInstance = ITemplate3(feeds[i]);
            feedInstance.submitPredval(predictions[i], stakes[i], epoch_start);
        }
    }

    ///@notice send predictiosn to one side, this is useful when an strtategy based on betting on both side is used but the same instance of predictoor can not submit to both sides of a feed
    function predict(bool side, uint256[] calldata stakes, address[] calldata feeds, uint256 epoch_start)
        external
        onlyMaster
    {
        uint256 n = stakes.length;
        for (uint256 i = 0; i < n; i++) {
            ITemplate3 feedInstance = ITemplate3(feeds[i]);
            feedInstance.submitPredval(side, stakes[i], epoch_start);
        }
    }

    ///@notice claim payouts from predictions
    function getPayout(uint256[] calldata epoch_start, address[] calldata feeds) external onlyMaster {
        uint256 n = feeds.length;
        for (uint256 i = 0; i < n; i++) {
            ITemplate3 feedInstance = ITemplate3(feeds[i]);
            feedInstance.payoutMultiple(epoch_start, address(this));
        }
    }

    ///@notice allows to transfer any ERC20 that may be in this contract to another address
    function transferERC20(address token, address to, uint256 amount) external onlyMaster {
        IERC20 tokenInstance = IERC20(token);
        tokenInstance.transfer(to, amount);
    }

    ///@notice allows tos end any native token in this contract to another address
    function transfer() external payable onlyMaster {
        (bool status,) = address(msg.sender).call{value: address(this).balance}("");
        require(status, "Failed transaction");
    }

    fallback() external payable {}

    receive() external payable {}
}