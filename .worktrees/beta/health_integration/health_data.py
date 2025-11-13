#!/usr/bin/env python3
"""
Health Data Integration Module

Integrates health data from Android Health Connect and Google Fit.
Part of v1.6.0 - Adaptive Reminders & Health Integration (Phase H).
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import os

# Try to import Android Health Connect SDK (via android-health-connect package)
try:
    from healthconnect import HealthConnectClient
    ANDROID_HEALTH_AVAILABLE = True
except ImportError:
    ANDROID_HEALTH_AVAILABLE = False

# Try to import Google Fit API
try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_FIT_AVAILABLE = True
except ImportError:
    GOOGLE_FIT_AVAILABLE = False


class HealthDataIntegrator:
    """Integrate health data from multiple sources"""
    
    GOOGLE_FIT_SCOPES = ['https://www.googleapis.com/auth/fitness.sleep.read',
                         'https://www.googleapis.com/auth/fitness.activity.read']
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.health_data_path = self.repo_root / ".copilot" / "health_data.json"
        self.health_data = self._load_health_data()
        
        self.sources = {
            "android_health": False,
            "google_fit": False,
            "manual_entry": True
        }
        
        self.android_health_client = None
        self.google_fit_service = None
    
    def _load_health_data(self) -> Dict[str, Any]:
        """Load health data"""
        if self.health_data_path.exists():
            with open(self.health_data_path, 'r') as f:
                return json.load(f)
        
        return {
            "sleep_records": [],
            "activity_records": [],
            "energy_levels": [],
            "location_history": []
        }
    
    def _save_health_data(self):
        """Save health data"""
        self.health_data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.health_data_path, 'w') as f:
            json.dump(self.health_data, f, indent=2)
    
    def connect_android_health(self, package_name: str = None) -> bool:
        """
        Connect to Android Health Connect API
        
        Requires:
        - Android Health Connect app installed
        - healthconnect package: pip install android-health-connect
        - Permissions granted in Android manifest
        
        Args:
            package_name: Your app's package name (e.g., 'com.yourapp.osmen')
        
        Returns:
            bool: True if connection successful
        """
        if not ANDROID_HEALTH_AVAILABLE:
            print("⚠️  Android Health Connect SDK not available")
            print("   Install: pip install android-health-connect")
            print("   Falling back to manual entry")
            return False
        
        try:
            # Initialize Android Health Connect client
            self.android_health_client = HealthConnectClient(package_name or "com.osmen.app")
            
            # Request permissions for sleep and activity data
            permissions = [
                "android.permission.health.READ_SLEEP",
                "android.permission.health.READ_STEPS",
                "android.permission.health.READ_DISTANCE",
            ]
            
            self.android_health_client.request_permissions(permissions)
            
            # Test connection by fetching recent sleep data
            test_data = self.android_health_client.read_records(
                record_type="Sleep",
                time_range_filter={
                    "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
                    "end_time": datetime.now().isoformat()
                }
            )
            
            self.sources["android_health"] = True
            print(f"✅ Android Health Connect connected (found {len(test_data)} records)")
            return True
            
        except Exception as e:
            print(f"❌ Android Health Connect failed: {e}")
            print("   Falling back to manual entry")
            return False
    
    def connect_google_fit(self, credentials_path: str = None, token_path: str = None) -> bool:
        """
        Connect to Google Fit API
        
        Requires:
        - Google Cloud project with Fitness API enabled
        - OAuth 2.0 credentials downloaded
        - google-api-python-client: pip install google-api-python-client google-auth-oauthlib
        
        Args:
            credentials_path: Path to OAuth credentials JSON
            token_path: Path to store access token
        
        Returns:
            bool: True if connection successful
        """
        if not GOOGLE_FIT_AVAILABLE:
            print("⚠️  Google Fit API libraries not available")
            print("   Install: pip install google-api-python-client google-auth-oauthlib")
            print("   Falling back to manual entry")
            return False
        
        try:
            credentials_path = credentials_path or os.getenv('GOOGLE_FIT_CREDENTIALS', 'google_fit_credentials.json')
            token_path = token_path or os.getenv('GOOGLE_FIT_TOKEN', 'google_fit_token.json')
            
            creds = None
            
            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.GOOGLE_FIT_SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(credentials_path):
                        print(f"❌ Credentials file not found: {credentials_path}")
                        print("   Download OAuth 2.0 credentials from Google Cloud Console")
                        print("   Falling back to manual entry")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, self.GOOGLE_FIT_SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Build Fitness service
            self.google_fit_service = build('fitness', 'v1', credentials=creds)
            
            # Test connection by fetching recent sleep data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.sleep.segment"
                }],
                "bucketByTime": {"durationMillis": 86400000},  # 1 day
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }
            
            response = self.google_fit_service.users().dataset().aggregate(
                userId="me", body=body).execute()
            
            self.sources["google_fit"] = True
            print(f"✅ Google Fit connected (found {len(response.get('bucket', []))} data buckets)")
            return True
            
        except Exception as e:
            print(f"❌ Google Fit connection failed: {e}")
            print("   Falling back to manual entry")
            return False
    
    def fetch_sleep_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch sleep data for past N days from all connected sources
        
        Tries Android Health Connect, Google Fit, then falls back to manual records
        
        Args:
            days: Number of days to fetch
            
        Returns:
            List of sleep records
        """
        sleep_records = []
        
        # Try Android Health Connect first
        if self.sources["android_health"] and self.android_health_client:
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                records = self.android_health_client.read_records(
                    record_type="Sleep",
                    time_range_filter={
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    }
                )
                
                for record in records:
                    # Parse Android Health Connect sleep record
                    start = datetime.fromisoformat(record["start_time"])
                    end = datetime.fromisoformat(record["end_time"])
                    duration_hours = (end - start).total_seconds() / 3600
                    
                    # Determine quality from sleep stages if available
                    quality = "good"
                    if "sleep_stages" in record:
                        deep_sleep_ratio = sum(1 for s in record["sleep_stages"] if s["stage"] == "deep") / len(record["sleep_stages"])
                        if deep_sleep_ratio > 0.25:
                            quality = "excellent"
                        elif deep_sleep_ratio < 0.15:
                            quality = "fair"
                    
                    sleep_records.append({
                        "date": start.strftime("%Y-%m-%d"),
                        "hours": round(duration_hours, 1),
                        "quality": quality,
                        "source": "android_health",
                        "timestamp": datetime.now().isoformat(),
                        "raw_data": record
                    })
                
                print(f"📱 Fetched {len(sleep_records)} sleep records from Android Health")
                
            except Exception as e:
                print(f"⚠️  Android Health fetch failed: {e}")
        
        # Try Google Fit if Android Health didn't return data
        if not sleep_records and self.sources["google_fit"] and self.google_fit_service:
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                body = {
                    "aggregateBy": [{
                        "dataTypeName": "com.google.sleep.segment"
                    }],
                    "bucketByTime": {"durationMillis": 86400000},  # 1 day buckets
                    "startTimeMillis": int(start_time.timestamp() * 1000),
                    "endTimeMillis": int(end_time.timestamp() * 1000)
                }
                
                response = self.google_fit_service.users().dataset().aggregate(
                    userId="me", body=body).execute()
                
                for bucket in response.get("bucket", []):
                    for dataset in bucket.get("dataset", []):
                        for point in dataset.get("point", []):
                            start_ms = int(point["startTimeNanos"]) / 1000000
                            end_ms = int(point["endTimeNanos"]) / 1000000
                            duration_hours = (end_ms - start_ms) / 3600000
                            
                            start_dt = datetime.fromtimestamp(start_ms / 1000)
                            
                            # Determine quality from sleep type
                            sleep_type = point.get("value", [{}])[0].get("intVal", 0)
                            quality_map = {
                                1: "poor",      # Awake
                                2: "fair",      # Sleep (light)
                                3: "good",      # Out of bed
                                4: "excellent"  # Light sleep
                            }
                            quality = quality_map.get(sleep_type, "good")
                            
                            sleep_records.append({
                                "date": start_dt.strftime("%Y-%m-%d"),
                                "hours": round(duration_hours, 1),
                                "quality": quality,
                                "source": "google_fit",
                                "timestamp": datetime.now().isoformat(),
                                "raw_data": point
                            })
                
                print(f"🏃 Fetched {len(sleep_records)} sleep records from Google Fit")
                
            except Exception as e:
                print(f"⚠️  Google Fit fetch failed: {e}")
        
        # Fall back to manual records if no API data
        if not sleep_records:
            sleep_records = self.health_data.get("sleep_records", [])[-days:]
            if sleep_records:
                print(f"📝 Using {len(sleep_records)} manual sleep records")
        
        return sleep_records
    
    def fetch_activity_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch activity/step data for past N days from connected sources
        
        Args:
            days: Number of days to fetch
            
        Returns:
            List of activity records with steps, distance, calories
        """
        activity_records = []
        
        # Try Android Health Connect
        if self.sources["android_health"] and self.android_health_client:
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                # Fetch steps
                step_records = self.android_health_client.read_records(
                    record_type="Steps",
                    time_range_filter={
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    }
                )
                
                for record in step_records:
                    date = datetime.fromisoformat(record["start_time"]).strftime("%Y-%m-%d")
                    activity_records.append({
                        "date": date,
                        "steps": record.get("count", 0),
                        "source": "android_health",
                        "timestamp": datetime.now().isoformat()
                    })
                
                print(f"📱 Fetched {len(activity_records)} activity records from Android Health")
                
            except Exception as e:
                print(f"⚠️  Android Health activity fetch failed: {e}")
        
        # Try Google Fit
        if not activity_records and self.sources["google_fit"] and self.google_fit_service:
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                body = {
                    "aggregateBy": [{
                        "dataTypeName": "com.google.step_count.delta",
                        "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
                    }],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": int(start_time.timestamp() * 1000),
                    "endTimeMillis": int(end_time.timestamp() * 1000)
                }
                
                response = self.google_fit_service.users().dataset().aggregate(
                    userId="me", body=body).execute()
                
                for bucket in response.get("bucket", []):
                    date = datetime.fromtimestamp(
                        int(bucket["startTimeMillis"]) / 1000
                    ).strftime("%Y-%m-%d")
                    
                    steps = 0
                    for dataset in bucket.get("dataset", []):
                        for point in dataset.get("point", []):
                            steps += point.get("value", [{}])[0].get("intVal", 0)
                    
                    activity_records.append({
                        "date": date,
                        "steps": steps,
                        "source": "google_fit",
                        "timestamp": datetime.now().isoformat()
                    })
                
                print(f"🏃 Fetched {len(activity_records)} activity records from Google Fit")
                
            except Exception as e:
                print(f"⚠️  Google Fit activity fetch failed: {e}")
        
        # Fall back to manual records
        if not activity_records:
            activity_records = self.health_data.get("activity_records", [])[-days:]
        
        return activity_records
    
    def record_manual_sleep(self, sleep_hours: float, quality: str,
                           date: datetime = None):
        """Manually record sleep data"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        record = {
            "date": date.strftime("%Y-%m-%d"),
            "hours": sleep_hours,
            "quality": quality,
            "source": "manual",
            "timestamp": datetime.now().isoformat()
        }
        
        self.health_data.setdefault("sleep_records", []).append(record)
        self._save_health_data()
    
    def record_manual_energy(self, energy_level: int, time_of_day: str = None):
        """Manually record energy level (1-10)"""
        if time_of_day is None:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 22:
                time_of_day = "evening"
            else:
                time_of_day = "night"
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "time_of_day": time_of_day,
            "level": min(10, max(1, energy_level)),
            "source": "manual"
        }
        
        self.health_data.setdefault("energy_levels", []).append(record)
        self._save_health_data()
    
    def get_average_sleep_hours(self, days: int = 7) -> float:
        """Get average sleep hours over past N days"""
        sleep_records = self.fetch_sleep_data(days)
        if not sleep_records:
            return 7.0
        
        total_hours = sum(r.get('hours', 0) for r in sleep_records)
        return total_hours / len(sleep_records)


class SleepPatternAnalyzer:
    """Analyze sleep patterns and their impact on productivity"""
    
    def __init__(self, health_integrator: HealthDataIntegrator):
        self.health = health_integrator
    
    def analyze_sleep_impact(self) -> Dict[str, Any]:
        """Analyze sleep's impact on productivity"""
        avg_sleep = self.health.get_average_sleep_hours(7)
        
        if avg_sleep >= 7 and avg_sleep <= 9:
            sleep_status = "optimal"
            productivity_impact = "positive"
        elif avg_sleep >= 6:
            sleep_status = "adequate"
            productivity_impact = "neutral"
        else:
            sleep_status = "insufficient"
            productivity_impact = "negative"
        
        recommendations = []
        if avg_sleep < 7:
            recommendations.append("Increase sleep to 7-9 hours for better focus")
        
        return {
            "average_sleep_hours": round(avg_sleep, 1),
            "sleep_status": sleep_status,
            "productivity_impact": productivity_impact,
            "recommendations": recommendations
        }


def main():
    print("Health Data Integration - Ready")


if __name__ == "__main__":
    main()
