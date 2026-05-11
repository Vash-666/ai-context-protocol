const { expect } = require("chai");
const hre = require("hardhat");

describe("TrophyNFT", function () {
  let trophyNFT;
  let owner;
  let addr1;
  let addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await hre.ethers.getSigners();

    const TrophyNFT = await hre.ethers.getContractFactory("TrophyNFT");
    trophyNFT = await TrophyNFT.deploy();
    await trophyNFT.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the correct name and symbol", async function () {
      expect(await trophyNFT.name()).to.equal("1947 Tennis Trophy");
      expect(await trophyNFT.symbol()).to.equal("TROPHY1947");
    });

    it("Should set the correct owner", async function () {
      expect(await trophyNFT.owner()).to.equal(owner.address);
    });

    it("Should start with total supply of 0", async function () {
      expect(await trophyNFT.totalSupply()).to.equal(0);
    });
  });

  describe("Minting", function () {
    it("Should allow owner to mint a trophy", async function () {
      const winners = ["Player A", "Player B", "Player C"];
      
      await expect(
        trophyNFT.mintTrophy(
          addr1.address,
          "ipfs://test-uri",
          "1947 Championship Trophy",
          "Historic tennis trophy",
          1947,
          winners,
          "Silver",
          "Tennis Club"
        )
      )
        .to.emit(trophyNFT, "TrophyMinted")
        .withArgs(1, addr1.address, "ipfs://test-uri", 1947, await getBlockTimestamp());

      expect(await trophyNFT.ownerOf(1)).to.equal(addr1.address);
      expect(await trophyNFT.totalSupply()).to.equal(1);
    });

    it("Should store correct trophy data", async function () {
      const winners = ["Player A", "Player B", "Player C"];
      
      await trophyNFT.mintTrophy(
        addr1.address,
        "ipfs://test-uri",
        "1947 Championship Trophy",
        "Historic tennis trophy",
        1947,
        winners,
        "Silver",
        "Tennis Club"
      );

      const data = await trophyNFT.getTrophyData(1);
      expect(data.name).to.equal("1947 Championship Trophy");
      expect(data.year).to.equal(1947);
      expect(data.material).to.equal("Silver");
      expect(data.currentCustodian).to.equal("Tennis Club");
    });

    it("Should not allow non-owner to mint", async function () {
      const winners = ["Player A"];
      
      await expect(
        trophyNFT.connect(addr1).mintTrophy(
          addr1.address,
          "ipfs://test-uri",
          "Test Trophy",
          "Description",
          1947,
          winners,
          "Gold",
          "Club"
        )
      ).to.be.revertedWithCustomError(trophyNFT, "OwnableUnauthorizedAccount");
    });
  });

  describe("Custodian Management", function () {
    beforeEach(async function () {
      const winners = ["Player A"];
      await trophyNFT.mintTrophy(
        addr1.address,
        "ipfs://test-uri",
        "Test Trophy",
        "Description",
        1947,
        winners,
        "Gold",
        "Original Club"
      );
    });

    it("Should allow owner to update custodian", async function () {
      await expect(trophyNFT.updateCustodian(1, "New Club"))
        .to.emit(trophyNFT, "CustodianUpdated")
        .withArgs(1, "Original Club", "New Club", await getBlockTimestamp());

      const data = await trophyNFT.getTrophyData(1);
      expect(data.currentCustodian).to.equal("New Club");
    });

    it("Should not allow non-owner to update custodian", async function () {
      await expect(
        trophyNFT.connect(addr1).updateCustodian(1, "New Club")
      ).to.be.revertedWithCustomError(trophyNFT, "OwnableUnauthorizedAccount");
    });

    it("Should not allow updating custodian for non-existent token", async function () {
      await expect(
        trophyNFT.updateCustodian(999, "New Club")
      ).to.be.revertedWith("TrophyNFT: Token does not exist");
    });
  });

  describe("Transfers", function () {
    beforeEach(async function () {
      const winners = ["Player A"];
      await trophyNFT.mintTrophy(
        addr1.address,
        "ipfs://test-uri",
        "Test Trophy",
        "Description",
        1947,
        winners,
        "Gold",
        "Club"
      );
    });

    it("Should emit TrophyTransferred event on transfer", async function () {
      await expect(
        trophyNFT.connect(addr1).transferFrom(addr1.address, addr2.address, 1)
      )
        .to.emit(trophyNFT, "TrophyTransferred")
        .withArgs(1, addr1.address, addr2.address, await getBlockTimestamp());
    });
  });

  describe("Winners", function () {
    it("Should return correct winners array", async function () {
      const winners = ["Player A", "Player B", "Player C", "Player D"];
      
      await trophyNFT.mintTrophy(
        addr1.address,
        "ipfs://test-uri",
        "Test Trophy",
        "Description",
        1947,
        winners,
        "Gold",
        "Club"
      );

      const retrievedWinners = await trophyNFT.getWinners(1);
      expect(retrievedWinners).to.deep.equal(winners);
    });
  });

  // Helper function
  async function getBlockTimestamp() {
    const block = await hre.ethers.provider.getBlock("latest");
    return block.timestamp;
  }
});
