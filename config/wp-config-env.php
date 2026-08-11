<?php
/**
 * RADMAN SILVER 925 — Secure Environment Loader for WordPress (wp-config-env.php)
 * 
 * STATUS: DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST
 * 
 * INSTRUCTIONS:
 * 1. Store your environment file outside the public web root (e.g., in an account-private .config directory).
 * 2. Set the environment variable RADMAN_ENV_FILE in your server/PHP-FPM config, or define RADMAN_ENV_FILE constant
 *    in wp-config.php before including this script.
 * 3. Require this file at the top of wp-config.php before ABSPATH / wp-settings.php.
 */

// Determine the explicit configurable absolute path to the environment secrets file:
$env_path = getenv('RADMAN_ENV_FILE');
if (!$env_path && defined('RADMAN_ENV_FILE')) {
    $env_path = RADMAN_ENV_FILE;
}

if (!$env_path) {
    header('HTTP/1.1 500 Internal Server Error');
    die('Critical Error: RADMAN_ENV_FILE is not specified. An explicit absolute path outside the web root is required.');
}

// Require the path to be outside common web roots:
if (strpos($env_path, '/public_html/') !== false || strpos($env_path, '/www/') !== false || strpos($env_path, __DIR__) !== false) {
    header('HTTP/1.1 500 Internal Server Error');
    die('Critical Error: Security violation. The environment file must be located outside the public web root.');
}

if (!file_exists($env_path) || !is_readable($env_path)) {
    header('HTTP/1.1 500 Internal Server Error');
    die('Critical Error: Environment configuration file is absent or unreadable. Secure host path required.');
}

// Parse INI using INI_SCANNER_RAW to prevent value mangling:
$dotenv = parse_ini_file($env_path, false, INI_SCANNER_RAW);
if (!is_array($dotenv)) {
    header('HTTP/1.1 500 Internal Server Error');
    die('Critical Error: Failed to parse environment configuration file.');
}

// Populate environment variables without logging secrets:
foreach ($dotenv as $key => $value) {
    putenv("$key=$value");
    $_ENV[$key] = $value;
    $_SERVER[$key] = $value;
}

// Validate required database variables:
$required_db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST'];
foreach ($required_db_vars as $var) {
    if (!isset($_ENV[$var]) || trim($_ENV[$var]) === '') {
        header('HTTP/1.1 500 Internal Server Error');
        die('Critical Error: Required database configuration variable missing or empty.');
    }
}

// Define WordPress database constants only if they are not already defined:
if (!defined('DB_NAME')) {
    define('DB_NAME', $_ENV['DB_NAME']);
}
if (!defined('DB_USER')) {
    define('DB_USER', $_ENV['DB_USER']);
}
if (!defined('DB_PASSWORD')) {
    define('DB_PASSWORD', $_ENV['DB_PASSWORD']);
}
if (!defined('DB_HOST')) {
    define('DB_HOST', $_ENV['DB_HOST']);
}
