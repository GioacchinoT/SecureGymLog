// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract GymLog is Ownable, Pausable {

    // Struttura per memorizzare l'hash dell'allenamento e il timestamp
    struct Workout {
        bytes32 docHash;
        uint256 timestamp;
    }

    // Mapping: Indirizzo dell'utente -> Array di allenamenti
    mapping(address => Workout[]) private workouts;

    event WorkoutSaved(address indexed user, bytes32 docHash, uint256 timestamp);

    constructor() Ownable(msg.sender) {}

    // Funzione per salvare l'hash (Off-chain storage pattern)
    function saveWorkout(bytes32 _docHash) public whenNotPaused {
        workouts[msg.sender].push(Workout(_docHash, block.timestamp));
        emit WorkoutSaved(msg.sender, _docHash, block.timestamp);
    }

    // Getter per recuperare i record di un utente
    function getWorkouts() public view returns (Workout[] memory) {
        return workouts[msg.sender];
    }

    // Circuit Breaker: funzione per bloccare il contratto in emergenza (Lezione 7)
    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }
}