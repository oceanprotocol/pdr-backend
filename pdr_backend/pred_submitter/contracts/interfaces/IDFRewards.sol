// SPDX-License-Identifier: None
pragma solidity ^0.8.13;

interface IDFRewards {
    function claimFor(
        address _to,
        address tokenAddress
    ) external returns (uint256);
}
