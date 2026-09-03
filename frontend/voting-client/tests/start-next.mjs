import os from "node:os";

os.networkInterfaces = () => ({
  lo: [
    {
      address: "127.0.0.1",
      family: "IPv4",
      internal: true,
      mac: "00:00:00:00:00:00",
      netmask: "255.0.0.0",
      cidr: "127.0.0.1/8",
    },
  ],
});
process.argv = ["node", "next", "start", "-H", "127.0.0.1", "-p", "3200"];
await import("next/dist/bin/next");
