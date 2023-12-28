module.exports = {
  apps : [{
    name   : "pm2-testnet-predictoor",
    script : "./pdr predictoor 3 ppss.yaml sapphire-testnet",
    env: {
      PRIVATE_KEY : "0xd0239747d5ba4b9bd9e9fd229b478710fd3fb8b2dc9215ab8b681136491d2b1e",
    }
  }]
}
