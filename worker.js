export default {
  async fetch(request, env) {
    // Serve static dashboard assets from public directory
    return env.ASSETS.fetch(request);
  }
};
