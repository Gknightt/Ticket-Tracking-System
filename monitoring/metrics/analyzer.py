"""
Metrics Analyzer
Analyzes performance data and generates comprehensive reports
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics

class MetricsAnalyzer:
    def __init__(self):
        self.logs_dir = Path(__file__).parent.parent / 'logs'
        self.performance_log = self.logs_dir / 'performance.log'
        self.entries = []
    
    def load_performance_logs(self):
        """Load performance log entries"""
        if not self.performance_log.exists():
            print("No performance logs found")
            return []
        
        try:
            with open(self.performance_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        self.entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error loading logs: {e}")
        
        return self.entries
    
    def calculate_statistics(self):
        """Calculate comprehensive statistics"""
        if not self.entries:
            return None
        
        # Group by endpoint
        by_endpoint = defaultdict(lambda: {
            'count': 0,
            'durations': [],
            'errors': 0
        })
        
        # Group by status code
        by_status = defaultdict(int)
        
        # All durations
        all_durations = []
        
        for entry in self.entries:
            endpoint = f"{entry['method']} {entry['path']}"
            duration = entry['duration']
            status = entry['status_code']
            
            by_endpoint[endpoint]['count'] += 1
            by_endpoint[endpoint]['durations'].append(duration)
            if status >= 400:
                by_endpoint[endpoint]['errors'] += 1
            
            by_status[status] += 1
            all_durations.append(duration)
        
        # Calculate percentiles
        sorted_durations = sorted(all_durations)
        n = len(sorted_durations)
        
        def percentile(p):
            k = (n - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < n:
                return sorted_durations[f] * (1 - c) + sorted_durations[f + 1] * c
            return sorted_durations[f]
        
        # Endpoint statistics
        endpoint_stats = []
        for endpoint, data in by_endpoint.items():
            durations = data['durations']
            sorted_d = sorted(durations)
            n_d = len(sorted_d)
            
            endpoint_stats.append({
                'endpoint': endpoint,
                'requests': data['count'],
                'avg_duration': round(sum(durations) / len(durations), 2),
                'min_duration': round(min(durations), 2),
                'max_duration': round(max(durations), 2),
                'p95_duration': round(sorted_d[int(n_d * 0.95)] if n_d > 0 else 0, 2),
                'error_rate': f"{(data['errors'] / data['count'] * 100):.2f}%"
            })
        
        endpoint_stats.sort(key=lambda x: x['requests'], reverse=True)
        
        total_errors = sum(1 for e in self.entries if e['status_code'] >= 400)
        
        return {
            'summary': {
                'total_requests': len(self.entries),
                'total_errors': total_errors,
                'error_rate': f"{(total_errors / len(self.entries) * 100):.2f}%",
                'avg_response_time': round(statistics.mean(all_durations), 2),
                'min_response_time': round(min(all_durations), 2),
                'max_response_time': round(max(all_durations), 2),
                'p50_response_time': round(percentile(0.50), 2),
                'p95_response_time': round(percentile(0.95), 2),
                'p99_response_time': round(percentile(0.99), 2),
            },
            'by_endpoint': endpoint_stats[:20],
            'by_status_code': dict(sorted(by_status.items(), key=lambda x: x[1], reverse=True)),
            'time_range': {
                'start': self.entries[0]['timestamp'],
                'end': self.entries[-1]['timestamp']
            }
        }
    
    def generate_report(self):
        """Generate and display report"""
        print("=" * 80)
        print("PERFORMANCE METRICS REPORT")
        print("=" * 80 + "\n")
        
        self.load_performance_logs()
        
        if not self.entries:
            print("No performance data available.")
            print("Make sure the performance middleware is enabled.\n")
            return
        
        stats = self.calculate_statistics()
        
        print("SUMMARY")
        print("-" * 80)
        for key, value in stats['summary'].items():
            print(f"{key.replace('_', ' ').title():25} {value}")
        
        print(f"\nTime Range:              {stats['time_range']['start']} to")
        print(f"                         {stats['time_range']['end']}")
        
        print("\n\nTOP ENDPOINTS (by request count)")
        print("-" * 80)
        print(f"{'Endpoint':<40} {'Requests':>10} {'Avg(ms)':>10} {'P95(ms)':>10} {'Errors':>10}")
        print("-" * 80)
        
        for ep in stats['by_endpoint']:
            print(f"{ep['endpoint']:<40} {ep['requests']:>10} {ep['avg_duration']:>10} "
                  f"{ep['p95_duration']:>10} {ep['error_rate']:>10}")
        
        print("\n\nSTATUS CODE DISTRIBUTION")
        print("-" * 80)
        total = stats['summary']['total_requests']
        for code, count in stats['by_status_code'].items():
            percentage = (count / total * 100)
            print(f"{code}: {count:>6} ({percentage:>5.2f}%)")
        
        # Save to file
        report_path = self.logs_dir / f"metrics-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n✓ Full report saved to: {report_path}\n")

if __name__ == '__main__':
    analyzer = MetricsAnalyzer()
    analyzer.generate_report()
