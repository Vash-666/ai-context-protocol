// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title TrophyNFT
 * @dev ERC-721 contract for tokenizing the 1947 Tennis Trophy
 * Represents a real-world asset (RWA) on the blockchain
 */
contract TrophyNFT is ERC721, ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;
    
    Counters.Counter private _tokenIdCounter;
    
    // Trophy metadata structure
    struct TrophyData {
        string name;
        string description;
        uint256 year;
        string[] winners;
        string material;
        string currentCustodian;
        uint256 mintedAt;
    }
    
    // Mapping from token ID to trophy data
    mapping(uint256 => TrophyData) public trophyData;
    
    // Events for provenance tracking
    event TrophyMinted(
        uint256 indexed tokenId,
        address indexed owner,
        string tokenURI,
        uint256 year,
        uint256 timestamp
    );
    
    event TrophyTransferred(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to,
        uint256 timestamp
    );
    
    event CustodianUpdated(
        uint256 indexed tokenId,
        string oldCustodian,
        string newCustodian,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor initializes the NFT collection
     */
    constructor() ERC721("1947 Tennis Trophy", "TROPHY1947") Ownable(msg.sender) {
        // Start token IDs at 1
        _tokenIdCounter.increment();
    }
    
    /**
     * @dev Mint a new trophy NFT
     * @param to Address to mint the token to
     * @param uri IPFS URI pointing to the metadata JSON
     * @param _name Trophy name
     * @param _description Trophy description
     * @param _year Year of the trophy (1947)
     * @param _winners Array of winner names engraved on the trophy
     * @param _material Material of the trophy (e.g., "Silver", "Gold")
     * @param _currentCustodian Current physical custodian of the trophy
     */
    function mintTrophy(
        address to,
        string memory uri,
        string memory _name,
        string memory _description,
        uint256 _year,
        string[] memory _winners,
        string memory _material,
        string memory _currentCustodian
    ) public onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        
        trophyData[tokenId] = TrophyData({
            name: _name,
            description: _description,
            year: _year,
            winners: _winners,
            material: _material,
            currentCustodian: _currentCustodian,
            mintedAt: block.timestamp
        });
        
        emit TrophyMinted(
            tokenId,
            to,
            uri,
            _year,
            block.timestamp
        );
        
        return tokenId;
    }
    
    /**
     * @dev Update the current custodian of the physical trophy
     * @param tokenId The token ID
     * @param newCustodian New custodian name/address
     */
    function updateCustodian(uint256 tokenId, string memory newCustodian) public onlyOwner {
        require(_exists(tokenId), "TrophyNFT: Token does not exist");
        
        string memory oldCustodian = trophyData[tokenId].currentCustodian;
        trophyData[tokenId].currentCustodian = newCustodian;
        
        emit CustodianUpdated(
            tokenId,
            oldCustodian,
            newCustodian,
            block.timestamp
        );
    }
    
    /**
     * @dev Get all winners for a trophy
     * @param tokenId The token ID
     * @return Array of winner names
     */
    function getWinners(uint256 tokenId) public view returns (string[] memory) {
        require(_exists(tokenId), "TrophyNFT: Token does not exist");
        return trophyData[tokenId].winners;
    }
    
    /**
     * @dev Get complete trophy data
     * @param tokenId The token ID
     * @return TrophyData struct with all trophy information
     */
    function getTrophyData(uint256 tokenId) public view returns (TrophyData memory) {
        require(_exists(tokenId), "TrophyNFT: Token does not exist");
        return trophyData[tokenId];
    }
    
    /**
     * @dev Override transfer to emit custom event
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        
        if (from != address(0) && to != address(0)) {
            emit TrophyTransferred(tokenId, from, to, block.timestamp);
        }
    }
    
    /**
     * @dev Override required functions
     */
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }
    
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }
    
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
    
    /**
     * @dev Get total number of trophies minted
     */
    function totalSupply() public view returns (uint256) {
        return _tokenIdCounter.current() - 1;
    }
}