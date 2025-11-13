// scripts/deploy.js
const { ethers } = require("hardhat");

async function main() {
  const Provenance = await ethers.getContractFactory("Provenance");
  console.log("Deploying Provenance contract...");

  const provenance = await Provenance.deploy(); // Deploy contract
  await provenance.waitForDeployment(); // Wait for deployment confirmation

  console.log("Provenance deployed to:", await provenance.getAddress());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
