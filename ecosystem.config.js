module.exports = {
  apps: [
    {
      name: "coding-questions-bot",
      script: "src/app.py",
      autorestart: false,
      interpreter: "poetry",
      interpreter_args: "run python",
      env: {
        PYTHONPATH: ".",
      },
      log_date_format: "YYYY-MM-DD HH:mm Z",
    },
  ],
};
