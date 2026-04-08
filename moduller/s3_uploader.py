from datetime import datetime
from pathlib import Path
import logging
import boto3
from botocore.config import Config
import os
import io
import json
import threading
from moduller.moduller.config_manager import config_manager
from moduller.moduller.upload_logger import (
    log_upload_attempt, log_upload_success, log_upload_failed,
    log_upload_retrying, log_upload_skipped, log_upload_timeout
)

logger = logging.getLogger(__name__)

# Module-level S3 config from config_manager (used by legacy functions)
_s3_config = config_manager.get_s3_credentials()
S3_BUCKET_NAME = _s3_config.get("bucket_name", "ddsfocustime")
S3_REGION = _s3_config.get("region", "us-east-1")

# ============================================
# CONTABO SHARED HELPER
# ============================================
# Centralized Contabo credentials (used by all Contabo upload functions)
_CONTABO_ACCESS_KEY = "6ea825cf4e68a7087af3d57f667dd66e"
_CONTABO_SECRET_KEY = "9cd10c8e7f0a4e32b8ba9cc044ba8027"
_CONTABO_HOSTNAME = "eu2.contabostorage.com"
_CONTABO_BUCKET = "focuspro"
_CONTABO_REGION = "eu2"

# Cloudflare Worker proxy — all Contabo uploads go through this to bypass ISP blocking
_CONTABO_PROXY_URL = "https://contabo-proxy.ddsfocuspro.workers.dev"
_CONTABO_PROXY_TOKEN = "ASD79138246asd#"


def _generate_contabo_presigned_url(contabo_key, content_type, expires_in=300):
    """Generate a pre-signed PUT URL for Contabo (local math, no network call)."""
    client = boto3.client(
        's3',
        aws_access_key_id=_CONTABO_ACCESS_KEY,
        aws_secret_access_key=_CONTABO_SECRET_KEY,
        endpoint_url=f"https://{_CONTABO_HOSTNAME}",
        region_name=_CONTABO_REGION,
        config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
    )
    return client.generate_presigned_url(
        'put_object',
        Params={'Bucket': _CONTABO_BUCKET, 'Key': contabo_key, 'ContentType': content_type},
        ExpiresIn=expires_in
    )


def _upload_to_contabo_async(data_bytes, contabo_key, content_type="application/json"):
    """
    Fire-and-forget Contabo mirror upload in a background daemon thread.
    Never blocks the calling function. Logs success/failure via upload_logger.
    """
    t = threading.Thread(
        target=_upload_to_contabo,
        args=(data_bytes, contabo_key, content_type),
        daemon=True
    )
    t.start()


def _upload_to_contabo(data_bytes, contabo_key, content_type="application/json", max_retries=3):
    """
    Upload data bytes to Contabo Object Storage with automatic retry.
    This is the shared helper used by all upload functions.
    Handles SSL, timeout, and connectivity errors with clear diagnostics.
    Retries up to max_retries times with exponential backoff on transient failures.
    
    Args:
        data_bytes: Raw bytes to upload
        contabo_key: The object key (path) in Contabo bucket
        content_type: MIME type (default: application/json)
        max_retries: Number of retry attempts (default: 3)
    
    Returns:
        str: Contabo URL if successful, None if failed
    """
    import time as _time

    # Extract email/task from contabo_key for logging (best-effort)
    _key_parts = contabo_key.split('/')
    _log_email = _key_parts[2] if len(_key_parts) > 2 else "unknown"
    _log_task = _key_parts[3] if len(_key_parts) > 3 else "unknown"
    _log_upload_type = _key_parts[0] if _key_parts else "unknown"  # e.g. users_screenshots, users_logs

    import urllib.request as _urllib_request
    import urllib.parse as _urllib_parse
    import ssl as _ssl
    import certifi as _certifi
    _ssl_ctx = _ssl.create_default_context(cafile=_certifi.where())

    data_size = len(data_bytes) if data_bytes else 0
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            log_upload_attempt("_upload_to_contabo", _log_upload_type, "CONTABO",
                               _log_email, _log_task, data_size_bytes=data_size,
                               s3_key=contabo_key, attempt=attempt, max_attempts=max_retries)
            print(f"[CONTABO] Attempt {attempt}/{max_retries} – Uploading {data_size} bytes via proxy, key={contabo_key} ...")

            # Generate pre-signed URL (local math, no network call)
            presigned_url = _generate_contabo_presigned_url(contabo_key, content_type)

            # URL-encode non-ASCII characters (Turkish ıüöçşğ etc.) to avoid UnicodeEncodeError
            safe_key = _urllib_parse.quote(contabo_key, safe='/')
            proxy_url = f"{_CONTABO_PROXY_URL}/{_CONTABO_BUCKET}/{safe_key}"
            req = _urllib_request.Request(proxy_url, data=data_bytes, method='PUT')
            req.add_header('Content-Type', content_type)
            req.add_header('X-Proxy-Token', _CONTABO_PROXY_TOKEN)
            req.add_header('X-Target-Url', _urllib_parse.quote(presigned_url, safe=':/?&=@%+'))
            req.add_header('User-Agent', 'DDSFocusPro/1.7')

            _t0 = _time.time()
            with _urllib_request.urlopen(req, timeout=60, context=_ssl_ctx) as resp:
                if resp.status not in (200, 201):
                    raise Exception(f"Proxy returned HTTP {resp.status}")
            _duration = _time.time() - _t0

            url = f"https://{_CONTABO_HOSTNAME}/{_CONTABO_BUCKET}/{contabo_key}"
            logger.info("Contabo upload successful via proxy (attempt %d): %s", attempt, url)
            print(f"[CONTABO OK] Upload successful via proxy (attempt {attempt}): {url}")
            log_upload_success("_upload_to_contabo", _log_upload_type, "CONTABO",
                               _log_email, _log_task, data_size_bytes=data_size,
                               s3_key=contabo_key, url=url, duration_sec=_duration,
                               attempt=attempt, max_attempts=max_retries)
            return url
        except Exception as e:
            last_error = e
            error_type = type(e).__name__
            error_msg = str(e)
            logger.warning("Contabo proxy upload attempt %d/%d failed for key %s: [%s] %s",
                           attempt, max_retries, contabo_key, error_type, error_msg)
            print(f"[CONTABO WARN] Attempt {attempt}/{max_retries} failed for {contabo_key}: [{error_type}] {error_msg}")

            if attempt < max_retries:
                backoff = min(2 ** attempt, 10)  # 2s, 4s, max 10s
                print(f"[CONTABO] Retrying in {backoff}s ...")
                log_upload_retrying("_upload_to_contabo", _log_upload_type, "CONTABO",
                                    _log_email, _log_task, error=f"[{error_type}] {error_msg}",
                                    attempt=attempt, max_attempts=max_retries, backoff_sec=backoff,
                                    s3_key=contabo_key)
                _time.sleep(backoff)

    # All retries exhausted
    if last_error:
        error_type = type(last_error).__name__
        error_msg = str(last_error)
        logger.error("Contabo upload FAILED after %d attempts for key %s: [%s] %s",
                     max_retries, contabo_key, error_type, error_msg)
        print(f"[CONTABO ERROR] Upload FAILED after {max_retries} attempts for {contabo_key}: [{error_type}] {error_msg}")
        log_upload_failed("_upload_to_contabo", _log_upload_type, "CONTABO",
                          _log_email, _log_task, error=f"[{error_type}] {error_msg}",
                          s3_key=contabo_key, attempt=max_retries, max_attempts=max_retries)

    return None


def get_s3_client():
    """Create and return an S3 client using config_manager credentials"""
    try:
        s3_config = config_manager.get_s3_credentials()
        access_key = s3_config.get("access_key")
        secret_key = s3_config.get("secret_key")
        bucket = s3_config.get("bucket_name", "ddsfocustime")
        region = s3_config.get("region", "us-east-1")

        if not all([access_key, secret_key, bucket, region]):
            logger.error("get_s3_client: Missing AWS credentials")
            return None

        timeout_config = Config(
            connect_timeout=10,
            read_timeout=30,
            retries={'max_attempts': 2}
        )
        client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=timeout_config
        )
        return client
    except Exception as e:
        logger.error("get_s3_client: Failed to create S3 client: %s", e)
        return None

def upload_activity_data_direct(activity_data, email, task_name, file_extension="json"):
    """
    Upload activity tracking data directly to S3 following screenshot pattern
    Structure: logs/{date}/{email}/activity_{task_name}_{timestamp}.json (one file per session)
    
    Args:
        activity_data: Dictionary containing activity tracking data
        email: User email
        task_name: Task name for filename
        file_extension: File extension (default: "json")
    
    Returns:
        str: S3 URL if successful, None if failed
    """
    logger.info("[upload_activity_data_direct] started")

    # Get S3 credentials from configuration manager (same as screenshots)
    s3_config = config_manager.get_s3_credentials()
    access_key = s3_config.get("access_key")
    secret_key = s3_config.get("secret_key")
    bucket = s3_config.get("bucket_name", "ddsfocustime")
    region = s3_config.get("region", "us-east-1")

    logger.info("Using S3 config from configuration manager")
    logger.info("S3_BUCKET_NAME: %s", bucket)
    logger.info("AWS_REGION: %s", region)

    # Check if credentials are missing
    if not all([access_key, secret_key, bucket, region]):
        logger.error("One or more AWS environment variables are missing.")
        log_upload_skipped("upload_activity_data_direct", "activity_data", "AWS_S3",
                           email, task_name, reason="Missing AWS credentials")
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    safe_email = email.replace("@", "_at_")
    safe_task_name = task_name.replace(" ", "_").replace("/", "_")
    filename = f"activity_{safe_task_name}_{timestamp}.{file_extension}"
    
    # Structure: users_logs/{date}/{email}/{task}/activity_{timestamp}.json (consistent with screenshot structure)
    s3_key = f"users_logs/{date_folder}/{safe_email}/{safe_task_name}/{filename}"

    logger.info("Email: %s", email)
    logger.info("Task: %s", task_name)
    logger.info("Activity Data: %d applications tracked", len(activity_data.get('applications', [])))
    logger.info("S3 key: %s", s3_key)

    try:
        # Convert activity data to JSON
        if isinstance(activity_data, dict) or isinstance(activity_data, list):
            activity_content = json.dumps(activity_data, indent=2, ensure_ascii=False)
        else:
            activity_content = str(activity_data)
        
        activity_bytes = activity_content.encode('utf-8')
        _data_size = len(activity_bytes)

        log_upload_attempt("upload_activity_data_direct", "activity_data", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3 = session.client('s3')
        
        # Upload activity data directly to S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=activity_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        logger.info("Activity data upload successful: %s", url)
        log_upload_success("upload_activity_data_direct", "activity_data", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=s3_key, url=url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(activity_bytes, s3_key, 'application/json')

        return url
    except Exception as e:
        logger.error("Activity data upload failed: %s", e)
        log_upload_failed("upload_activity_data_direct", "activity_data", "AWS_S3",
                          email, task_name, error=str(e), s3_key=s3_key)
        return None


def upload_logs_direct(log_data, email, task_name, log_type="session_log", file_extension="json"):
    """
    Upload logs directly to S3 following the same pattern as screenshots
    
    Args:
        log_data: Dictionary or string containing the log data
        email: User email
        task_name: Task name
        log_type: Type of log (default: "session_log")
        file_extension: File extension (default: "json")
    
    Returns:
        str: S3 URL if successful, None if failed
    """
    logger.info("[upload_logs_direct] started")

    # Get S3 credentials from configuration manager (same as screenshots)
    s3_config = config_manager.get_s3_credentials()
    access_key = s3_config.get("access_key")
    secret_key = s3_config.get("secret_key")
    bucket = s3_config.get("bucket_name", "ddsfocustime")
    region = s3_config.get("region", "us-east-1")

    logger.info("Using S3 config from configuration manager")
    logger.info("S3_BUCKET_NAME: %s", bucket)
    logger.info("AWS_REGION: %s", region)

    # Check if credentials are missing
    if not all([access_key, secret_key, bucket, region]):
        logger.error(" One or more AWS environment variables are missing.")
        log_upload_skipped("upload_logs_direct", log_type, "AWS_S3",
                           email, task_name, reason="Missing AWS credentials")
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    safe_email = email.replace("@", "_at_")
    safe_task = task_name.replace(" ", "_").replace("/", "_")
    filename = f"{log_type}_{timestamp}.{file_extension}"
    
    # Use the same structure as users_screenshots but with users_logs
    s3_key = f"users_logs/{date_folder}/{safe_email}/{safe_task}/{filename}"

    logger.info("Email: %s", email)
    logger.info("Task: %s", task_name)
    logger.info("Log Type: %s", log_type)
    logger.info("S3 key: %s", s3_key)

    try:
        # Convert log data to JSON if it's a dictionary
        if isinstance(log_data, dict) or isinstance(log_data, list):
            log_content = json.dumps(log_data, indent=2, ensure_ascii=False)
        else:
            log_content = str(log_data)
        
        log_bytes = log_content.encode('utf-8')
        _data_size = len(log_bytes)

        log_upload_attempt("upload_logs_direct", log_type, "AWS_S3",
                           email, task_name, data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3 = session.client('s3')
        
        # Upload log data directly to S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=log_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        logger.info("Log upload successful: %s", url)
        log_upload_success("upload_logs_direct", log_type, "AWS_S3",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=s3_key, url=url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(log_bytes, s3_key, 'application/json')

        return url
    except Exception as e:
        logger.error("Log upload failed: %s", e)
        log_upload_failed("upload_logs_direct", log_type, "AWS_S3",
                          email, task_name, error=str(e), s3_key=s3_key)
        return None


def upload_screenshot_direct(image_bytes, email, task_name, file_extension="webp", s3_key_override=None):
    """
    Upload screenshot directly to S3 without saving to local file first
    
    Args:
        image_bytes: Raw image bytes (from PIL image.save() or similar)
        email: User email
        task_name: Task name
        file_extension: File extension (default: webp)
        s3_key_override: Optional pre-built S3 key (ensures same key as Contabo)
    
    Returns:
        str: S3 URL if successful, None if failed
    """
    logger.info("[upload_screenshot_direct] started")

    # Get S3 credentials from configuration manager
    s3_config = config_manager.get_s3_credentials()
    access_key = s3_config.get("access_key")
    secret_key = s3_config.get("secret_key")
    bucket = s3_config.get("bucket_name", "ddsfocustime")
    region = s3_config.get("region", "us-east-1")

    logger.info("Using S3 config from configuration manager")
    logger.info("S3_BUCKET_NAME: %s", bucket)
    logger.info("AWS_REGION: %s", region)
    logger.info("ACCESS_KEY (first 8 chars): %s***", access_key[:8] if access_key else "None")
    logger.info("SECRET_KEY (length): %d chars", len(secret_key) if secret_key else 0)

    # Check if credentials are missing
    if not all([access_key, secret_key, bucket, region]):
        logger.error("One or more AWS environment variables are missing.")
        logger.error("access_key: %s", "Present" if access_key else "Missing")
        logger.error("secret_key: %s", "Present" if secret_key else "Missing")
        logger.error("bucket: %s", "Present" if bucket else "Missing")
        logger.error("region: %s", "Present" if region else "Missing")
        log_upload_skipped("upload_screenshot_direct", "screenshot", "AWS_S3",
                           email, task_name, reason="Missing AWS credentials")
        return None

    if s3_key_override:
        s3_key = s3_key_override
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        safe_email = email.replace("@", "_at_")
        safe_task = task_name.replace(" ", "_").replace("/", "_")
        filename = f"{timestamp}.{file_extension}"
        s3_key = f"users_screenshots/{date_folder}/{safe_email}/{safe_task}/{filename}"

    logger.info("Email: %s", email)
    logger.info("Task: %s", task_name)
    logger.info("S3 key: %s", s3_key)

    _data_size = len(image_bytes) if image_bytes else 0
    log_upload_attempt("upload_screenshot_direct", "screenshot", "AWS_S3",
                       email, task_name, data_size_bytes=_data_size, s3_key=s3_key)

    try:
        from botocore.config import Config
        import time as _time
        s3_timeout_config = Config(
            connect_timeout=10,
            read_timeout=30,
            retries={'max_attempts': 2}
        )
        _t0 = _time.time()
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3 = session.client('s3', config=s3_timeout_config)
        
        # Upload bytes directly to S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=image_bytes,
            ContentType=f'image/{file_extension}'
        )
        _duration = _time.time() - _t0

        url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        logger.info("Direct upload successful: %s", url)
        log_upload_success("upload_screenshot_direct", "screenshot", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=s3_key, url=url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(image_bytes, s3_key, f'image/{file_extension}')

        return url
    except Exception as e:
        if "InvalidAccessKeyId" in str(e):
            logger.error("AWS ACCESS KEY INVALID: %s", str(e))
            logger.error("Please update your AWS credentials in .env file:")
            logger.error("   - Generate new Access Key in AWS IAM Console")
            logger.error("   - Update S3_ACCESS_KEY and S3_SECRET_KEY in .env")
            logger.error("   - Restart the application")
        else:
            logger.error("Direct upload failed: %s", e)
        log_upload_failed("upload_screenshot_direct", "screenshot", "AWS_S3",
                          email, task_name, error=str(e), data_size_bytes=_data_size, s3_key=s3_key)
        return None

def upload_screenshot(local_path, email, task_name):
    logger.info("[upload_screenshot] started")

    # Check boto3
    logger.info("boto3 module already imported at top")

    # Load AWS credentials from environment variables
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket = os.getenv("S3_BUCKET_NAME", "ddsfocustime")
    region = os.getenv("AWS_REGION", "us-east-1")


    logger.info("AWS_ACCESS_KEY_ID: %s", access_key)
    logger.info("S3_BUCKET_NAME: %s", bucket)
    logger.info("AWS_REGION: %s", region)

    # Check if credentials are missing
    if not all([access_key, secret_key, bucket, region]):
        logger.error("One or more AWS environment variables are missing.")
        log_upload_skipped("upload_screenshot", "screenshot", "AWS_S3",
                           email, task_name, reason="Missing AWS credentials")
        return None

    # Check if local file exists
    if not Path(local_path).exists():
        logger.error("File not found: %s", local_path)
        log_upload_skipped("upload_screenshot", "screenshot", "AWS_S3",
                           email, task_name, reason=f"File not found: {local_path}")
        return None

    filename = Path(local_path).name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    safe_email = email.replace("@", "_at_")
    safe_task = task_name.replace(" ", "_").replace("/", "_")
    s3_key = f"users_screenshots/{date_folder}/{safe_email}/{safe_task}/{timestamp}_{filename}"

    logger.info("Local file: %s", local_path)
    logger.info("Email: %s", email)
    logger.info("Task: %s", task_name)
    logger.info("S3 key: %s", s3_key)

    _file_size = os.path.getsize(str(local_path)) if os.path.exists(str(local_path)) else 0
    log_upload_attempt("upload_screenshot", "screenshot", "AWS_S3",
                       email, task_name, data_size_bytes=_file_size, s3_key=s3_key)

    try:
        import time as _time
        _t0 = _time.time()
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3 = session.client('s3')
        s3.upload_file(str(local_path), bucket, s3_key)
        _duration = _time.time() - _t0

        url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        logger.info("Upload successful: %s", url)
        log_upload_success("upload_screenshot", "screenshot", "AWS_S3",
                           email, task_name, data_size_bytes=_file_size,
                           s3_key=s3_key, url=url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        try:
            with open(str(local_path), 'rb') as f:
                file_bytes = f.read()
            _upload_to_contabo_async(file_bytes, s3_key, f'image/{Path(local_path).suffix.lstrip(".")}')
        except Exception as contabo_err:
            logger.warning("Contabo mirror failed for %s: %s", s3_key, contabo_err)

        return url
    except Exception as e:
        logger.error("Upload failed: %s", e)
        log_upload_failed("upload_screenshot", "screenshot", "AWS_S3",
                          email, task_name, error=str(e), data_size_bytes=_file_size, s3_key=s3_key)
        return None


def upload_daily_log_file_to_s3(email, date, daily_log, task_name="general"):
    """
    Upload/create the main daily log file to S3 following users_screenshots pattern
    Structure: logs/{date_folder}/{safe_email}/{safe_task}/{timestamp}_{filename}
    Returns the S3 URL if successful, None if failed
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            log_upload_skipped("upload_daily_log_file_to_s3", "daily_log", "AWS_S3",
                               email, task_name, reason="Could not create S3 client")
            return None
            
        # Follow the same pattern as users_screenshots
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        safe_email = email.replace('@', '_at_').replace('.', '_')
        
        # Skip the default task selection - use "general" instead
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            
        safe_task = task_name.replace(" ", "_").replace("/", "_")
        filename = f"daily_log_{timestamp}.json"
        
        # Use the same structure as users_screenshots but with logs/
        s3_key = f"logs/{date_folder}/{safe_email}/{safe_task}/{filename}"
        
        # Convert daily log to JSON
        log_json = json.dumps(daily_log, indent=2, ensure_ascii=False)
        _log_bytes = log_json.encode('utf-8')
        _data_size = len(_log_bytes)

        log_upload_attempt("upload_daily_log_file_to_s3", "daily_log", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=_log_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        print(f"Daily log file created in S3: {s3_url}")
        log_upload_success("upload_daily_log_file_to_s3", "daily_log", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=s3_key, url=s3_url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(_log_bytes, s3_key, 'application/json')
        
        return s3_url
        
    except Exception as e:
        print(f"Failed to upload daily log file to S3: {e}")
        log_upload_failed("upload_daily_log_file_to_s3", "daily_log", "AWS_S3",
                          email, task_name, error=str(e))
        return None


def append_to_daily_log_file(email, activity_entry):
    """
    Append activity to existing daily log file in S3
    Returns the S3 URL if successful, None if failed
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            log_upload_skipped("append_to_daily_log_file", "daily_log_append", "AWS_S3",
                               email, "general", reason="Could not create S3 client")
            return None
            
        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Convert email to safe filename format
        safe_email = email.replace('@', '_at_').replace('.', '_')
        
        # Create S3 key for daily log file
        s3_key = f"logs/{current_date}/{safe_email}/daily_log_{current_date}.json"
        
        try:
            # Try to get existing file
            response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            existing_log = json.loads(response['Body'].read().decode('utf-8'))
        except s3_client.exceptions.NoSuchKey:
            # File doesn't exist, create new structure
            existing_log = {
                "date": current_date,
                "email": email,
                "created_at": datetime.now().isoformat(),
                "activities": []
            }
        
        # Append new activity
        existing_log["activities"].append(activity_entry)
        existing_log["last_updated"] = datetime.now().isoformat()
        
        # Convert back to JSON
        log_json = json.dumps(existing_log, indent=2, ensure_ascii=False)
        _log_bytes = log_json.encode('utf-8')
        _data_size = len(_log_bytes)

        log_upload_attempt("append_to_daily_log_file", "daily_log_append", "AWS_S3",
                           email, "general", data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        # Upload updated file back to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=_log_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        print(f"Activity appended to daily log: {s3_url}")
        log_upload_success("append_to_daily_log_file", "daily_log_append", "AWS_S3",
                           email, "general", data_size_bytes=_data_size,
                           s3_key=s3_key, url=s3_url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(_log_bytes, s3_key, 'application/json')
        
        return s3_url
        
    except Exception as e:
        print(f"Failed to append to daily log file: {e}")
        log_upload_failed("append_to_daily_log_file", "daily_log_append", "AWS_S3",
                          email, "general", error=str(e))
        return None


def upload_activity_log_to_s3(email, activity_log, task_name="general"):
    """
    Upload real-time activity log to S3 following users_screenshots pattern
    Structure: logs/{date_folder}/{safe_email}/{safe_task}/{timestamp}_{filename}
    Returns the S3 URL if successful, None if failed
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            log_upload_skipped("upload_activity_log_to_s3", "activity_log", "AWS_S3",
                               email, task_name, reason="Could not create S3 client")
            return None
            
        # Follow the same pattern as users_screenshots
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        safe_email = email.replace('@', '_at_').replace('.', '_')
        
        # Skip the default task selection - use "general" instead
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            
        safe_task = task_name.replace(" ", "_").replace("/", "_")
        filename = f"activity_log_{timestamp}.json"
        
        # Add active window information if available
        try:
            from .active_window_tracker import get_current_activity_summary
            window_summary = get_current_activity_summary()
            activity_log['active_windows_summary'] = window_summary
        except ImportError:
            activity_log['active_windows_summary'] = None
        
        # Use the same structure as users_screenshots but with logs/
        s3_key = f"logs/{date_folder}/{safe_email}/{safe_task}/{filename}"
        
        # Convert activity log to JSON
        log_json = json.dumps(activity_log, indent=2, ensure_ascii=False)
        _log_bytes = log_json.encode('utf-8')
        _data_size = len(_log_bytes)

        log_upload_attempt("upload_activity_log_to_s3", "activity_log", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=_log_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        print(f" Activity log uploaded to S3: {s3_url}")
        log_upload_success("upload_activity_log_to_s3", "activity_log", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=s3_key, url=s3_url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(_log_bytes, s3_key, 'application/json')
        
        return s3_url
        
    except Exception as e:
        print(f" Failed to upload activity log to S3: {e}")
        log_upload_failed("upload_activity_log_to_s3", "activity_log", "AWS_S3",
                          email, task_name, error=str(e))
        return None


def upload_program_tracking_to_s3(email, tracking_data, task_name="general"):
    """
    Upload program tracking data to S3 following exact users_screenshots pattern
    Structure: logs/{date_folder}/{safe_email}/{safe_task}/session_{start_time}_to_{end_time}.json
    Returns the S3 URL if successful, None if failed
    """
    try:
        # Get S3 credentials from configuration manager (same as other functions)
        s3_config = config_manager.get_s3_credentials()
        access_key = s3_config.get("access_key")
        secret_key = s3_config.get("secret_key")
        bucket = s3_config.get("bucket_name", "ddsfocustime")
        region = s3_config.get("region", "us-east-1")

        # Check if credentials are missing
        if not all([access_key, secret_key, bucket, region]):
            print(" One or more AWS credentials are missing.")
            log_upload_skipped("upload_program_tracking_to_s3", "program_tracking", "AWS_S3",
                               email, task_name, reason="Missing AWS credentials")
            return None
            
        # Skip the default task selection - use "general" instead
        if task_name in ["-- İş Emri Seçin --", "-- Select a Task --", "--_İş_Emri_Seçin_--"]:
            task_name = "general"
            
        # Create meaningful filename for single session
        date_folder = datetime.now().strftime("%Y-%m-%d")
        safe_email = email.replace('@', '_at_').replace('.', '_')
        safe_task = task_name.replace(" ", "_").replace("/", "_").replace("-", "_")
        
        # Use session start/end times for filename if available
        session_start = tracking_data.get('session_start', datetime.now().isoformat())
        session_end = tracking_data.get('session_end', datetime.now().isoformat())
        
        try:
            start_time = datetime.fromisoformat(session_start.replace('Z', '')).strftime("%H-%M-%S")
            end_time = datetime.fromisoformat(session_end.replace('Z', '')).strftime("%H-%M-%S")
            filename = f"session_{start_time}_to_{end_time}.json"
        except:
            # Fallback to timestamp if parsing fails
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"session_{timestamp}.json"
        
        # Use the same structure as users_screenshots but with logs/
        s3_key = f"logs/{date_folder}/{safe_email}/{safe_task}/{filename}"
        
        # Convert tracking data to JSON
        tracking_json = json.dumps(tracking_data, indent=2, ensure_ascii=False)
        _tracking_bytes = tracking_json.encode('utf-8')
        _data_size = len(_tracking_bytes)

        log_upload_attempt("upload_program_tracking_to_s3", "program_tracking", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        # Create S3 client and upload
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=_tracking_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        print(f" Program tracking uploaded to S3: {s3_url}")
        log_upload_success("upload_program_tracking_to_s3", "program_tracking", "AWS_S3",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=s3_key, url=s3_url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(_tracking_bytes, s3_key, 'application/json')
        
        return s3_url
        
    except Exception as e:
        print(f" Failed to upload program tracking to S3: {e}")
        log_upload_failed("upload_program_tracking_to_s3", "program_tracking", "AWS_S3",
                          email, task_name, error=str(e))
        import traceback
        traceback.print_exc()
        return None


def upload_daily_logs_report(email, report_data, report_type="session_complete"):
    """
    Upload daily logs report to S3 in JSON format
    
    S3 Structure: logs/{date}/{email}/daily_activity_report_{timestamp}.json
    
    Args:
        email: User email
        report_data: Dictionary or list containing the log data
        report_type: Type of report (default: "session_complete")
    
    Returns:
        str: S3 URL if successful, None if failed
    """
    logger.info("[upload_daily_logs_report] started")

    # Try to get S3 credentials from configuration manager first
    try:
        s3_config = config_manager.get_s3_credentials()
        access_key = s3_config.get("access_key")
        secret_key = s3_config.get("secret_key")
        bucket = s3_config.get("bucket_name", "ddsfocustime")
        region = s3_config.get("region", "us-east-1")
        logger.info("Using S3 config from configuration manager")
    except:
        # Fallback to environment variables with standard AWS names
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket = os.getenv("S3_BUCKET_NAME", "ddsfocustime")
        region = os.getenv("AWS_REGION", "us-east-1")
        logger.info("Using S3 config from environment variables")

    logger.info("S3_BUCKET_NAME: %s", bucket)
    logger.info("AWS_REGION: %s", region)

    # Check if credentials are missing
    if not all([access_key, secret_key, bucket, region]):
        logger.error("One or more AWS environment variables are missing.")
        log_upload_skipped("upload_daily_logs_report", report_type, "AWS_S3",
                           email, "general", reason="Missing AWS credentials")
        return None

    # Create timestamp and date folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    safe_email = email.replace("@", "_at_").replace(".", "_")
    filename = f"{report_type}_report_{timestamp}.json"
    
    # S3 key structure: logs/date/email/filename.json
    s3_key = f"logs/{date_folder}/{safe_email}/{filename}"

    logger.info("Email: %s", email)
    logger.info("Report Type: %s", report_type)
    logger.info("S3 key: %s", s3_key)

    try:
        import json
        
        # Convert report data to JSON string
        json_data = json.dumps(report_data, indent=2, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        _data_size = len(json_bytes)

        log_upload_attempt("upload_daily_logs_report", report_type, "AWS_S3",
                           email, "general", data_size_bytes=_data_size, s3_key=s3_key)

        import time as _time
        _t0 = _time.time()
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3 = session.client('s3')
        
        # Upload JSON data directly to S3
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json_bytes,
            ContentType='application/json'
        )
        _duration = _time.time() - _t0

        url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        logger.info("Daily logs report upload successful: %s", url)
        log_upload_success("upload_daily_logs_report", report_type, "AWS_S3",
                           email, "general", data_size_bytes=_data_size,
                           s3_key=s3_key, url=url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(json_bytes, s3_key, 'application/json')

        return url
    except Exception as e:
        logger.error("Daily logs report upload failed: %s", e)
        log_upload_failed("upload_daily_logs_report", report_type, "AWS_S3",
                          email, "general", error=str(e), s3_key=s3_key)
        return None


def upload_employee_logs_batch(employees_logs_data, report_date=None):
    """
    Upload logs for multiple employees in batch
    
    Args:
        employees_logs_data: Dict with email as key and logs data as value
        report_date: Date string (YYYY-MM-DD), defaults to today
    
    Returns:
        list: List of uploaded URLs and status
    """
    logger.info("[upload_employee_logs_batch] started")
    
    if report_date is None:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    results = []
    
    for email, logs_data in employees_logs_data.items():
        try:
            # Add metadata to logs
            enhanced_logs = {
                "report_date": report_date,
                "employee_email": email,
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(logs_data) if isinstance(logs_data, list) else 1,
                "data": logs_data
            }
            
            url = upload_daily_logs_report(email, enhanced_logs, "daily_activity")
            
            if url:
                results.append({
                    "email": email,
                    "status": "success",
                    "url": url,
                    "entries_count": enhanced_logs["total_entries"]
                })
                logger.info("Uploaded logs for %s: %d entries", email, enhanced_logs["total_entries"])
            else:
                results.append({
                    "email": email,
                    "status": "failed",
                    "url": None,
                    "error": "Upload failed"
                })
                logger.error("Failed to upload logs for %s", email)
                
        except Exception as e:
            results.append({
                "email": email,
                "status": "error",
                "url": None,
                "error": str(e)
            })
            logger.error("Error processing logs for %s: %s", email, e)
    
    logger.info("Batch upload complete: %d employees processed", len(results))
    return results

# ============================================
# CONTABO OBJECT STORAGE FUNCTIONS
# ============================================

def upload_screenshot_to_contabo(image_bytes, email, task_name, file_extension="webp", contabo_key_override=None):
    """
    Upload screenshot to Contabo Object Storage (S3-compatible)
    Uses same folder structure as S3: users_screenshots/{date}/{email}/{task}/
    
    Args:
        image_bytes: Raw image bytes
        email: User email
        task_name: Task name
        file_extension: File extension (default: webp)
        contabo_key_override: Optional pre-built key (ensures same key as S3)
    
    Returns:
        str: Contabo URL if successful, None if failed
    """
    logger.info("[upload_screenshot_to_contabo] started")
    print(f"[CONTABO] upload_screenshot_to_contabo called for {email}, task={task_name}")

    if contabo_key_override:
        contabo_key = contabo_key_override
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        safe_email = email.replace("@", "_at_")
        safe_task = task_name.replace(" ", "_").replace("/", "_")
        filename = f"{timestamp}.{file_extension}"
        contabo_key = f"users_screenshots/{date_folder}/{safe_email}/{safe_task}/{filename}"

    logger.info("Email: %s", email)
    logger.info("Task: %s", task_name)
    logger.info("Contabo key: %s", contabo_key)

    _data_size = len(image_bytes) if image_bytes else 0

    # _upload_to_contabo already handles retries internally (3 attempts with backoff)
    # No outer retry loop needed — avoids 3×3 = 9 retries and excessive wait times
    log_upload_attempt("upload_screenshot_to_contabo", "screenshot", "CONTABO",
                       email, task_name, data_size_bytes=_data_size, s3_key=contabo_key)
    result = _upload_to_contabo(image_bytes, contabo_key, f'image/{file_extension}')
    if result:
        log_upload_success("upload_screenshot_to_contabo", "screenshot", "CONTABO",
                           email, task_name, data_size_bytes=_data_size,
                           s3_key=contabo_key, url=result)
        return result

    logger.error("Contabo screenshot upload failed for %s", contabo_key)
    print(f"[CONTABO ERROR] Screenshot upload FAILED for {contabo_key}")
    log_upload_failed("upload_screenshot_to_contabo", "screenshot", "CONTABO",
                      email, task_name, error="Upload failed after retries",
                      data_size_bytes=_data_size, s3_key=contabo_key)
    return None


def upload_logs_to_contabo(log_data, email, task_name, log_type="session_log", file_extension="json"):
    """
    Upload logs to Contabo Object Storage
    Uses same folder structure as S3: users_logs/{date}/{email}/{task}/
    
    Args:
        log_data: Dictionary or string containing the log data
        email: User email
        task_name: Task name
        log_type: Type of log (default: "session_log")
        file_extension: File extension (default: "json")
    
    Returns:
        str: Contabo URL if successful, None if failed
    """
    logger.info("[upload_logs_to_contabo] started")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    safe_email = email.replace("@", "_at_")
    safe_task = task_name.replace(" ", "_").replace("/", "_")
    filename = f"{log_type}_{timestamp}.{file_extension}"
    contabo_key = f"users_logs/{date_folder}/{safe_email}/{safe_task}/{filename}"

    logger.info("Contabo key: %s", contabo_key)

    try:
        # Convert log data to JSON if needed
        if isinstance(log_data, dict) or isinstance(log_data, list):
            log_content = json.dumps(log_data, indent=2, ensure_ascii=False)
        else:
            log_content = str(log_data)
        
        log_bytes = log_content.encode('utf-8')
        _data_size = len(log_bytes)
        log_upload_attempt("upload_logs_to_contabo", log_type, "CONTABO",
                           email, task_name, data_size_bytes=_data_size, s3_key=contabo_key)
        result = _upload_to_contabo(log_bytes, contabo_key, 'application/json')
        if result:
            log_upload_success("upload_logs_to_contabo", log_type, "CONTABO",
                               email, task_name, data_size_bytes=_data_size,
                               s3_key=contabo_key, url=result)
        else:
            log_upload_failed("upload_logs_to_contabo", log_type, "CONTABO",
                              email, task_name, error="_upload_to_contabo returned None",
                              data_size_bytes=_data_size, s3_key=contabo_key)
        return result
    except Exception as e:
        logger.error("Contabo log upload failed: %s", e)
        log_upload_failed("upload_logs_to_contabo", log_type, "CONTABO",
                          email, task_name, error=str(e), s3_key=contabo_key)
        return None


def test_contabo_connection():
    """
    Diagnostic function: test Contabo connectivity via Cloudflare Worker proxy.
    Call this from the console to verify the proxy is reachable and uploads work.
    Returns True if upload succeeded, False otherwise.
    """
    print("=" * 60)
    print("[CONTABO TEST] Starting Contabo proxy connectivity test...")
    print(f"  Proxy    : {_CONTABO_PROXY_URL}")
    print(f"  Bucket   : {_CONTABO_BUCKET}")
    print(f"  Region   : {_CONTABO_REGION}")
    print(f"  AccessKey: {_CONTABO_ACCESS_KEY[:8]}***")
    print("=" * 60)

    test_key = "test/contabo_proxy_test.txt"
    test_data = f"Contabo proxy test - {datetime.now().isoformat()}".encode('utf-8')

    try:
        print(f"[CONTABO TEST] Uploading test file via proxy to {test_key} ...")
        result = _upload_to_contabo(test_data, test_key, 'text/plain', max_retries=1)
        if result:
            print("=" * 60)
            print("[CONTABO TEST] PASSED - Proxy upload working correctly!")
            print(f"[CONTABO TEST] URL: {result}")
            print("=" * 60)
            return True
        else:
            print("[CONTABO TEST] FAILED - Upload returned None")
            return False
    except Exception as e:
        print(f"[CONTABO TEST] FAILED: {e}")
        return False


def upload_upload_log_to_s3(email, target_date=None):
    """
    Upload the local upload_log_{date}.txt file to both AWS S3 and Contabo.
    
    S3 folder structure:
        upload_logs/{date}/{safe_email}/upload_log_{date}.txt
    
    Only ONE file per user per day — overwrites if called again the same day.
    
    Args:
        email: User email address
        target_date: Date string (YYYY-MM-DD). Defaults to today.
    
    Returns:
        dict with 's3_url' key if successful, None if failed
    """
    import time as _time
    from .upload_logger import get_today_log_path

    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")

    # Locate the local upload log file
    log_file_path = get_today_log_path()
    if not os.path.exists(log_file_path):
        logger.warning("Upload log file not found: %s", log_file_path)
        log_upload_skipped("upload_upload_log_to_s3", "upload_log", "AWS_S3",
                           email, "system", reason="Local upload log file not found")
        return None

    try:
        s3_client = get_s3_client()
        if not s3_client:
            log_upload_skipped("upload_upload_log_to_s3", "upload_log", "AWS_S3",
                               email, "system", reason="Could not create S3 client")
            return None

        # Read the local log file
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()

        log_bytes = log_content.encode("utf-8")
        data_size = len(log_bytes)

        # Build S3 key: upload_logs/{date}/{safe_email}/upload_log_{date}.txt
        safe_email = email.replace("@", "_at_").replace(".", "_")
        s3_key = f"upload_logs/{target_date}/{safe_email}/upload_log_{target_date}.txt"

        log_upload_attempt("upload_upload_log_to_s3", "upload_log", "AWS_S3",
                           email, "system", data_size_bytes=data_size, s3_key=s3_key)

        _t0 = _time.time()
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=log_bytes,
            ContentType="text/plain"
        )
        _duration = _time.time() - _t0

        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        print(f"Upload log uploaded to S3: {s3_url}")
        log_upload_success("upload_upload_log_to_s3", "upload_log", "AWS_S3",
                           email, "system", data_size_bytes=data_size,
                           s3_key=s3_key, url=s3_url, duration_sec=_duration)

        # Mirror to Contabo in background thread (non-blocking)
        _upload_to_contabo_async(log_bytes, s3_key, "text/plain")

        return {"s3_url": s3_url, "s3_key": s3_key, "size_bytes": data_size}

    except Exception as e:
        print(f"Failed to upload upload log to S3: {e}")
        log_upload_failed("upload_upload_log_to_s3", "upload_log", "AWS_S3",
                          email, "system", error=str(e))
        return None