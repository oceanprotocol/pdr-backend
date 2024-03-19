// SPDX-License-Identifier: None
pragma solidity ^0.8.13;

import "./interfaces/IERC20.sol";
import "./PredSubmitter.sol";

contract PredSubmitterManager {
    PredSubmitter public instanceUp;
    PredSubmitter public instanceDown;
    address public immutable oceanTokenAddr;
    address public immutable owner;

    constructor(address oceanTokenAddr_) {
        instanceUp = new PredSubmitter();
        instanceDown = new PredSubmitter();
        instanceUp.initialize(msg.sender, oceanTokenAddr_);
        instanceDown.initialize(msg.sender, oceanTokenAddr_);

        oceanTokenAddr = oceanTokenAddr_;
        owner = msg.sender;
    }

    ///@notice access control
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner has access");
        _;
    }

    ///@notice send ocean tokens to the instances managed by the master
    function _sendTokensToInstance(uint256 amtUp, uint256 amtDown) internal {
        IERC20 tokenInstance = IERC20(oceanTokenAddr);
        if (amtUp != 0) tokenInstance.transfer(address(instanceUp), amtUp);
        if (amtDown != 0)
            tokenInstance.transfer(address(instanceDown), amtDown);
    }

    ///@notice claims DF rewards from the DFRewards contract
    function claimDFRewards(
        address tokenAddress,
        address dfRewards
    ) external onlyOwner {
        instanceUp.claimDFRewards(tokenAddress, dfRewards);
        instanceDown.claimDFRewards(tokenAddress, dfRewards);
    }

    ///@notice claim tokens from the instances
    function _getTokensFromInstance(
        address token,
        uint256 amtUp,
        uint256 amtDown
    ) internal {
        if (amtUp != 0) {
            instanceUp.transferERC20(token, address(this), amtUp);
        }
        if (amtDown != 0) {
            instanceDown.transferERC20(token, address(this), amtDown);
        }
    }

    ///@notice returns the contract version
    function version() external pure returns (string memory) {
        return "0.1.0";
    }

    ///@notice claim native tokens form the instances
    function getNativeTokenFromInstance() external onlyOwner {
        instanceUp.transfer();
        instanceDown.transfer();
    }

    ///@notice submit two-sided predicitons
    function submit(
        uint256[] calldata stakesUp,
        uint256[] calldata stakesDown,
        address[] calldata feeds,
        uint256 epoch
    ) external onlyOwner {
        uint256 upInstanceFunding = 0;
        uint256 downInstanceFunding = 0;

        for (uint256 i = 0; i < stakesUp.length; i++) {
            upInstanceFunding += stakesUp[i];
        }

        for (uint256 i = 0; i < stakesDown.length; i++) {
            downInstanceFunding += stakesDown[i];
        }

        _sendTokensToInstance(upInstanceFunding, downInstanceFunding);

        instanceUp.predict(true, stakesUp, feeds, epoch);
        instanceDown.predict(false, stakesDown, feeds, epoch);
    }

    ///@notice claim payouts for given feeds and epochs
    function getPayout(
        uint256[] calldata epochs,
        address[] calldata feeds
    ) external onlyOwner {
        instanceUp.getPayout(epochs, feeds);
        instanceDown.getPayout(epochs, feeds);

        IERC20 ocean = IERC20(oceanTokenAddr);
        uint256 balUp = ocean.balanceOf(address(instanceUp));
        uint256 balDown = ocean.balanceOf(address(instanceDown));

        _getTokensFromInstance(oceanTokenAddr, balUp, balDown);
    }

    /// @notice transfer any ERC20 tokens in this contract to another address
    function transferERC20(
        address token,
        address to,
        uint256 amount
    ) external onlyOwner {
        IERC20 tokenInstance = IERC20(token);
        tokenInstance.transfer(to, amount);
    }

    /// @notice transfer native tokens from this contract to an addrdess
    function transfer() external payable onlyOwner {
        (bool status, ) = address(msg.sender).call{
            value: address(this).balance
        }("");
        require(status, "Failed transaction");
    }

    /// @notice approves tokens from the instances to the feeds
    function approveOcean(address[] calldata feeds) external onlyOwner {
        instanceUp.approveOcean(feeds);
        instanceDown.approveOcean(feeds);
    }

    fallback() external payable {}

    receive() external payable {}
}
