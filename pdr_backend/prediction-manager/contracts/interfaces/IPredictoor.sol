// SPDX-License-Identifier: None
pragma solidity ^0.8.13;
    
interface IPredictoor {

    function initialize(address owner_, address oceanTokenAddr_) external;

    function approveOcean(address[] calldata feeds) external;

    function getCurEpoch(address feed) external view returns (uint256); 

    function predict(bool[] calldata predictions, uint256[] calldata stakes, address[] calldata feeds, uint256 epoch_start) external;
    
    function predict(bool side, uint256[] calldata stakes, address[] calldata feeds, uint256 epoch_start) external; 

    function getPayout(uint256[] calldata epoch_start, address[] calldata feeds) external; 

    function getStartTime(address feed) external view returns (uint256); 

    function transferERC20(address token, address to, uint256 amount) external; 

    function transfer() external payable;

}