[previous code remains unchanged until line 272]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) #Try to get port from environment variable, default to 5000
    try:
        logger.info(f"Starting Flask server on port {port}...")
        logger.debug("Debug mode is enabled")
        logger.debug("Current working directory: %s", os.getcwd())
        logger.debug("Environment variables: %s", str(dict(os.environ)))
        app.run(host='0.0.0.0', port=port, debug=True)
    except OSError as e:
        if e.errno == 98: #Address already in use error
            logger.critical(f"Failed to start Flask server: Port {port} is already in use. \n{traceback.format_exc()}")
        else:
            logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise
