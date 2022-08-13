module.exports = {
  apps: [
    {
      name: "coding-questions-bot",
      script: "src/main.py",
      autorestart: false,
      interpreter: "poetry",
      interpreter_args: "run python",
      env: {
        PYTHONPATH: ".",
      },
    },
  ],
};
