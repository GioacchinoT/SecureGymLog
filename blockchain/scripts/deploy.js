const hre = require("hardhat");

async function main() {
  const GymLog = await hre.ethers.getContractFactory("GymLog");
  const gymLog = await GymLog.deploy();
  
  await gymLog.waitForDeployment();
  console.log("GymLog distribuito all'indirizzo:", await gymLog.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});