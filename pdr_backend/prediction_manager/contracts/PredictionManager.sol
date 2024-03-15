// SPDX-License-Identifier: None
pragma solidity ^0.8.13;

import "./interfaces/IERC20.sol";
import "./Predictoor.sol";

contract PredictionManager {
    Predictoor public instance_up;
    Predictoor public instance_down;
    address public immutable oceanTokenAddr;
    address public immutable owner;

    constructor(address oceanTokenAddr_) {
        instance_up = new Predictoor();
        instance_down = new Predictoor();
        instance_up.initialize(msg.sender, oceanTokenAddr_);
        instance_down.initialize(msg.sender, oceanTokenAddr_);
        
        oceanTokenAddr = oceanTokenAddr_;
        owner = msg.sender;
    }

    ///@notice access control
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner has access");
        _;
    }

    ///@notice send ocean tokens to the instances managed by the master
    function sendTokensToInstance(uint256 amtUp, uint256 amtDown) internal onlyOwner {
        IERC20 tokenInstance = IERC20(oceanTokenAddr);
        if (amtUp != 0) tokenInstance.transfer(address(instance_up), amtUp);
        if (amtDown != 0) tokenInstance.transfer(address(instance_down), amtDown);
    }

    ///@notice claim tokens from the instances
    function getTokensFromInstance(address token, uint256 amtUp, uint256 amtDown) internal onlyOwner {
        if (amtUp != 0) {
            instance_up.transferERC20(token, address(this), amtUp);
        }
        if (amtDown != 0) {
            instance_down.transferERC20(token, address(this), amtDown);
        }
    }

    ///@notice claim native tokens form the instances
    function getNativeTokenFromInstance() external onlyOwner {
        instance_up.transfer();
        instance_down.transfer();
    }

    ///@notice submit predictions for the strategy of betting on both sides
    function submit(
        uint256[] calldata stakesUp,
        uint256[] calldata stakesDown,
        address[] calldata feeds,
        uint256 epoch_start
    ) external onlyOwner {
        instance_up.predict(true, stakesUp, feeds, epoch_start);
        instance_down.predict(false, stakesDown, feeds, epoch_start);
    }

    ///@notice claim payouts for the strategy of betting on both sides
    function getPayout(uint256[] calldata epoch_start, address[] calldata feeds) external onlyOwner {
        instance_up.getPayout(epoch_start, feeds);
        instance_down.getPayout(epoch_start, feeds);

        IERC20 ocean = IERC20(oceanTokenAddr);
        instance_up.transferERC20(oceanTokenAddr, address(this), ocean.balanceOf(address(instance_up)));
        instance_down.transferERC20(oceanTokenAddr, address(this), ocean.balanceOf(address(instance_down)));
    }

    /// @notice transfer any ERC20 tokens in this contract to another address
    function transferERC20(address token, address to, uint256 amount) external onlyOwner {
        IERC20 tokenInstance = IERC20(token);
        tokenInstance.transfer(to, amount);
    }

    /// @notice transfer native tokens from this contract to an addrdess
    function transfer() external payable onlyOwner {
        (bool status,) = address(msg.sender).call{value: address(this).balance}("");
        require(status, "Failed transaction");
    }

    /// @notice approves tokens from the instances to the feeds
    function approveOcean(address[] calldata feeds) external onlyOwner {
        instance_up.approveOcean(feeds);
        instance_down.approveOcean(feeds);
    }

    fallback() external payable {}

    receive() external payable {}
}
