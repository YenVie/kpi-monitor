"""
ALERT SYSTEM - HỆ THỐNG CẢNH BÁO
=================================
Gửi alert khi phát hiện suy giảm KPI
"""

import json
from datetime import datetime
from typing import List, Dict
import os

class AlertSystem:
    """Hệ thống gửi cảnh báo"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'email_enabled': False,
            'email_recipients': [],
            'slack_enabled': False,
            'slack_webhook': None,
            'save_to_file': True,
            'alert_file': 'alerts/alerts.json'
        }
        self.alerts_history = []
        
        # Tạo thư mục alerts nếu chưa có
        if self.config['save_to_file']:
            os.makedirs(os.path.dirname(self.config['alert_file']), exist_ok=True)
    
    def send_alert(self, alert_data: Dict, severity: str = 'warning'):
        """
        Gửi alert
        
        Args:
            alert_data: Dict chứa thông tin alert
            severity: Mức độ (info, warning, critical)
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'data': alert_data
        }
        
        # Lưu vào history
        self.alerts_history.append(alert)
        
        # Gửi qua các channel
        if self.config['save_to_file']:
            self._save_to_file(alert)
        
        if self.config['email_enabled']:
            self._send_email(alert)
        
        if self.config['slack_enabled']:
            self._send_slack(alert)
        
        # Print console
        self._print_alert(alert)
    
    def send_decline_alert(self, province: str, kpi: str, 
                          decline_pct: float, latest_value: float,
                          compare_value: float):
        """Gửi alert về suy giảm KPI"""
        severity = 'critical' if decline_pct < -10 else \
                   'warning' if decline_pct < -5 else 'info'
        
        alert_data = {
            'type': 'KPI_DECLINE',
            'province': province,
            'kpi': kpi,
            'decline_pct': decline_pct,
            'latest_value': latest_value,
            'compare_value': compare_value,
            'message': f'{province}: {kpi} suy giảm {decline_pct:.2f}%'
        }
        
        self.send_alert(alert_data, severity)
    
    def send_batch_alerts(self, alerts: List[Dict]):
        """Gửi nhiều alerts cùng lúc"""
        print(f"\n📢 Gửi {len(alerts)} alerts...")
        
        for alert in alerts:
            self.send_decline_alert(
                alert['province'],
                alert['kpi'],
                alert['decline_pct'],
                alert['latest_value'],
                alert['compare_value']
            )
    
    def _save_to_file(self, alert: Dict):
        """Lưu alert vào file JSON"""
        # Đọc alerts hiện có
        alerts_file = self.config['alert_file']
        
        if os.path.exists(alerts_file):
            with open(alerts_file, 'r', encoding='utf-8') as f:
                all_alerts = json.load(f)
        else:
            all_alerts = []
        
        # Thêm alert mới
        all_alerts.append(alert)
        
        # Lưu lại
        with open(alerts_file, 'w', encoding='utf-8') as f:
            json.dump(all_alerts, f, ensure_ascii=False, indent=2)
    
    def _send_email(self, alert: Dict):
        """Gửi email (cần implement)"""
        # TODO: Implement email sending
        # Có thể dùng: smtplib, sendgrid, AWS SES, etc.
        pass
    
    def _send_slack(self, alert: Dict):
        """Gửi Slack notification (cần implement)"""
        # TODO: Implement Slack webhook
        # import requests
        # requests.post(self.config['slack_webhook'], json=alert)
        pass
    
    def _print_alert(self, alert: Dict):
        """In alert ra console"""
        severity_icons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        icon = severity_icons.get(alert['severity'], '📢')
        data = alert['data']
        
        print(f"\n{icon} ALERT [{alert['severity'].upper()}]")
        print(f"   Time: {alert['timestamp']}")
        print(f"   {data.get('message', 'No message')}")
        if 'province' in data:
            print(f"   Province: {data['province']}")
            print(f"   KPI: {data['kpi']}")
            print(f"   Decline: {data['decline_pct']:.2f}%")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Lấy alerts trong N giờ gần đây"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for alert in self.alerts_history:
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if alert_time >= cutoff_time:
                recent.append(alert)
        
        return recent

