<?php
/**
 * RADMAN SILVER 925 — Secure .env Environment Loader for WordPress
 * 
 * INSTRUCTIONS:
 * Add this snippet at the top of your wp-config.php (before 'require_once ABSPATH . "wp-settings.php";')
 * so that MySQL database credentials and API secrets are read from the root .env file.
 */

if (file_exists(__DIR__ . '/.env')) {  
    $dotenv = parse_ini_file(__DIR__ . '/.env');  
    foreach ($dotenv as $key => $value) {  
        putenv("$key=$value");  
        $_ENV[$key] = $value;  
        $_SERVER[$key] = $value;  
    }  
}  
define('DB_NAME', getenv('DB_NAME'));  
define('DB_USER', getenv('DB_USER'));  
define('DB_PASSWORD', getenv('DB_PASSWORD'));  
define('DB_HOST', getenv('DB_HOST'));  
