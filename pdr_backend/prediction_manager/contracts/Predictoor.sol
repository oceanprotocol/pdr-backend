// SPDX-License-Identifier: None
pragma solidity ^0.8.13;

import "./interfaces/IERC20.sol";
import "./interfaces/IFeedContract.sol";
import "./interfaces/IDFRewards.sol";

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
        require(
            msg.sender == master || msg.sender == owner,
            "Only owner or master can access"
        );
        _;
    }

    ///@notice approve unlimited ocean tokens to the feeds
    function approveOcean(address[] calldata feeds) public onlyMaster {
        IERC20 ocean = IERC20(oceanTokenAddr);
        uint256 n = feeds.length;
        for (uint256 i = 0; i < n; i++) {
            ocean.approve(feeds[i], (2 ** 256) - 1);
        }
    }

    ///@notice returns the contract version
    function version() external pure returns (string memory) {
        return "0.1.0";
    }

    ///@notice claims DF rewards from the DFRewards contract
    function claimDFRewards(
        address tokenAddress,
        address dfRewards
    ) external onlyMaster {
        IDFRewards dfRewardsInstance = IDFRewards(dfRewards);
        dfRewardsInstance.claimFor(address(this), tokenAddress);
    }

    ///@notice send predictions (up and down) to each side
    function predict(
        bool[] calldata predictions,
        uint256[] calldata stakes,
        address[] calldata feeds,
        uint256 epoch_start
    ) external onlyMaster {
        uint256 n = predictions.length;
        for (uint256 i = 0; i < n; i++) {
            IFeedContract feedInstance = IFeedContract(feeds[i]);
            feedInstance.submitPredval(predictions[i], stakes[i], epoch_start);
        }
    }

    ///@notice send predictions to one side
    function predict(
        bool side,
        uint256[] calldata stakes,
        address[] calldata feeds,
        uint256 epoch_start
    ) external onlyMaster {
        uint256 n = stakes.length;
        for (uint256 i = 0; i < n; i++) {
            IFeedContract feedInstance = IFeedContract(feeds[i]);
            feedInstance.submitPredval(side, stakes[i], epoch_start);
        }
    }

    ///@notice claim payouts from predictions
    function getPayout(
        uint256[] calldata epoch_start,
        address[] calldata feeds
    ) external onlyMaster {
        uint256 n = feeds.length;
        for (uint256 i = 0; i < n; i++) {
            IFeedContract feedInstance = IFeedContract(feeds[i]);
            feedInstance.payoutMultiple(epoch_start, address(this));
        }
    }

    ///@notice allows to transfer any ERC20 that from the contract to given address
    function transferERC20(
        address token,
        address to,
        uint256 amount
    ) external onlyMaster {
        IERC20 tokenInstance = IERC20(token);
        tokenInstance.transfer(to, amount);
    }

    ///@notice allows to send native token in this contract to given address
    function transfer() external payable onlyMaster {
        (bool status, ) = address(msg.sender).call{
            value: address(this).balance
        }("");
        require(status, "Failed transaction");
    }

    fallback() external payable {}

    receive() external payable {}
}
