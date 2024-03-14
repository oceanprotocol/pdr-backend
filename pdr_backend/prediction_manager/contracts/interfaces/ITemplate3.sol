// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

interface ITemplate3 {
    struct Prediction {
        bool predictedValue;
        uint256 stake;
        address predictoor;
        bool paid;
    }

    enum Status {
        Pending,
        Paying,
        Canceled
    }

    function secondsPerEpoch() external view returns (uint256);

    function toEpochStart(uint256 _timestamp) external view returns (uint256);

    function curEpoch() external view returns (uint256);

    function soonestEpochToPredict(uint256 prediction_ts) external view returns (uint256);

    function submittedPredval(uint256 epoch_start, address predictoor) external view returns (bool);

    function getTotalStake(uint256 epoch_start) external view returns (uint256);

    function submitPredval(bool predictedValue, uint256 stake, uint256 epoch_start) external;

    function payoutMultiple(uint256[] calldata blocknums, address predictoor_addr) external;

    function payout(uint256 epoch_start, address predictoor_addr) external;

    function epochStatus(uint256 epoch) external view returns (Status);
}