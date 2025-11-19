"""
Database Performance Analyzer
Runs performance queries and generates reports
"""

import psycopg2
import json
import os
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

class DatabaseAnalyzer:
    def __init__(self):
        self.conn = None
        self.results = {}
        self.output_dir = Path(__file__).parent.parent / 'logs'
        self.output_dir.mkdir(exist_ok=True)
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'ticketdb'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres')
            )
            print("✓ Connected to database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def run_query(self, name, query):
        """Execute a query and store results"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            self.results[name] = {
                'columns': columns,
                'rows': rows,
                'count': len(rows)
            }
            
            print(f"✓ {name}: {len(rows)} rows")
            return True
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            return False
    
    def analyze_table_sizes(self):
        """Analyze table sizes and row counts"""
        query = """
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size,
            n_live_tup AS rows
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size('public.'||tablename) DESC
        LIMIT 10;
        """
        self.run_query('table_sizes', query)
    
    def analyze_index_usage(self):
        """Analyze index usage"""
        query = """
        SELECT
            tablename,
            indexname,
            idx_scan AS scans,
            pg_size_pretty(pg_relation_size(indexrelid)) AS size
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC
        LIMIT 10;
        """
        self.run_query('index_usage', query)
    
    def analyze_cache_hit_ratio(self):
        """Calculate cache hit ratio"""
        query = """
        SELECT
            sum(heap_blks_hit)::float / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100 
            AS cache_hit_ratio
        FROM pg_statio_user_tables;
        """
        self.run_query('cache_hit_ratio', query)
    
    def analyze_connections(self):
        """Get active connection count"""
        query = """
        SELECT
            count(*) as total_connections,
            count(CASE WHEN state = 'active' THEN 1 END) as active,
            count(CASE WHEN state = 'idle' THEN 1 END) as idle
        FROM pg_stat_activity
        WHERE datname = current_database();
        """
        self.run_query('connections', query)
    
    def generate_report(self):
        """Generate a formatted report"""
        report_path = self.output_dir / f'db-analysis-{datetime.now().strftime("%Y%m%d-%H%M%S")}.txt'
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("DATABASE PERFORMANCE ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for name, data in self.results.items():
                f.write(f"\n{name.upper().replace('_', ' ')}\n")
                f.write("-" * 80 + "\n")
                
                if data['rows']:
                    table = tabulate(data['rows'], headers=data['columns'], tablefmt='grid')
                    f.write(table + "\n")
                else:
                    f.write("No data\n")
        
        print(f"\n✓ Report saved to: {report_path}")
        
        # Also save as JSON
        json_path = self.output_dir / f'db-analysis-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        with open(json_path, 'w') as f:
            json_data = {
                name: {
                    'columns': data['columns'],
                    'rows': [list(row) for row in data['rows']]
                }
                for name, data in self.results.items()
            }
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"✓ JSON data saved to: {json_path}")
    
    def run_full_analysis(self):
        """Run all analysis queries"""
        print("\n" + "=" * 80)
        print("Running Database Performance Analysis")
        print("=" * 80 + "\n")
        
        if not self.connect():
            return
        
        self.analyze_table_sizes()
        self.analyze_index_usage()
        self.analyze_cache_hit_ratio()
        self.analyze_connections()
        
        self.generate_report()
        
        if self.conn:
            self.conn.close()
            print("\n✓ Database connection closed")

if __name__ == '__main__':
    analyzer = DatabaseAnalyzer()
    analyzer.run_full_analysis()
