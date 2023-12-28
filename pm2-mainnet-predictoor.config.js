module.exports = {
  apps : [{
    name   : "pm2-mainnet-predictoor",
    script : "./pdr predictoor 3 ppss.yaml sapphire-mainnet",
    env: {
      PRIVATE_KEY : "<YOUR_PRIVATE_KEY>",
    }
  }]
}
