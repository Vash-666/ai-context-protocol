const hre = require("hardhat");

async function main() {
  console.log("Deploying TrophyNFT contract...");

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  console.log("Account balance:", (await deployer.provider.getBalance(deployer.address)).toString());

  const TrophyNFT = await hre.ethers.getContractFactory("TrophyNFT");
  const trophyNFT = await TrophyNFT.deploy();

  await trophyNFT.waitForDeployment();

  const address = await trophyNFT.getAddress();
  console.log("TrophyNFT deployed to:", address);
  console.log("Transaction hash:", trophyNFT.deploymentTransaction().hash);

  // Verify on Etherscan if on a public network
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("Waiting for block confirmations...");
    await trophyNFT.deploymentTransaction().wait(5);
    
    try {
      await hre.run("verify:verify", {
        address: address,
        constructorArguments: [],
      });
      console.log("Contract verified on Etherscan");
    } catch (error) {
      console.log("Verification failed:", error.message);
    }
  }

  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    contractName: "TrophyNFT",
    address: address,
    network: hre.network.name,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    transactionHash: trophyNFT.deploymentTransaction().hash
  };

  fs.writeFileSync(
    "deployment-info.json",
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\nDeployment complete!");
  console.log("Contract address:", address);
  console.log("Network:", hre.network.name);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
