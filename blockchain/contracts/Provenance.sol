// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Provenance {
    event RecordLogged(uint256 indexed recordId, string operation, string recordHash);

    // Use mapping instead of array
    mapping(uint256 => string) public recordHashes;

    struct Record {
        string operation;
        string recordHash;
        uint256 timestamp;
        address user;
    }

    mapping(uint256 => Record) public records; // optional detailed structure

    function logAction(uint256 recordId, string memory operation, string memory recordHash) public {
        records[recordId] = Record(operation, recordHash, block.timestamp, msg.sender);
        recordHashes[recordId] = recordHash;
        emit RecordLogged(recordId, operation, recordHash);
    }

    function getRecordHash(uint256 recordId) public view returns (string memory) {
        return recordHashes[recordId];
    }

    function getRecordDetails(uint256 recordId)
        public
        view
        returns (string memory operation, string memory recordHash, uint256 timestamp, address user)
    {
        Record memory r = records[recordId];
        return (r.operation, r.recordHash, r.timestamp, r.user);
    }
}
