#!/usr/bin/env python3
"""
Web Server Log Analyzer
Analyzes Apache and Nginx log files to extract statistics and generate detailed reports.
Supports both Common Log Format (CLF) and Combined Log Format.
"""

import re
import json
import argparse
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class LogAnalyzer:
    """Analyzes web server log files and generates statistics."""

    # Regex patterns for different log formats
    APACHE_COMBINED = re.compile(
        r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\w+) (?P<endpoint>[^\s]+) HTTP/[\d\.]+" '
        r'(?P<status>\d+) (?P<bytes>[\d-]+)'
    )

    NGINX_COMBINED = re.compile(
        r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\w+) (?P<endpoint>[^\s]+) HTTP/[\d\.]+" '
        r'(?P<status>\d+) (?P<bytes>[\d-]+)'
    )

    # Alternative pattern for logs with additional fields
    EXTENDED_FORMAT = re.compile(
        r'(?P<ip>[\d\.]+) - (?P<user>[\w-]+) \[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\w+) (?P<endpoint>[^\s]+) HTTP/[\d\.]+" '
        r'(?P<status>\d+) (?P<bytes>[\d-]+)'
    )

    def __init__(self, error_threshold: int = 10, error_rate_threshold: float = 0.5):
        """
        Initialize the log analyzer.

        Args:
            error_threshold: Minimum number of errors to flag an IP as suspicious
            error_rate_threshold: Minimum error rate (0-1) to flag an IP as suspicious
        """
        self.error_threshold = error_threshold
        self.error_rate_threshold = error_rate_threshold

        # Statistics storage
        self.total_requests = 0
        self.ip_requests = defaultdict(int)
        self.ip_errors = defaultdict(int)
        self.endpoints = Counter()
        self.status_codes = Counter()
        self.methods = Counter()
        self.failed_lines = []

    def parse_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single log line.

        Args:
            line: Raw log line

        Returns:
            Dictionary with parsed fields or None if parsing fails
        """
        line = line.strip()
        if not line:
            return None

        # Try different patterns
        for pattern in [self.APACHE_COMBINED, self.NGINX_COMBINED, self.EXTENDED_FORMAT]:
            match = pattern.match(line)
            if match:
                return match.groupdict()

        return None

    def process_log_file(self, filepath: str) -> None:
        """
        Process a log file and extract statistics.

        Args:
            filepath: Path to the log file
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filepath}")

        print(f"📁 Processing log file: {filepath.name}")
        print(f"{'=' * 80}")

        line_count = 0
        parsed_count = 0

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_count += 1

                    parsed = self.parse_line(line)
                    if parsed:
                        self._update_statistics(parsed)
                        parsed_count += 1
                    else:
                        # Store failed lines for debugging
                        if len(self.failed_lines) < 10:  # Keep only first 10
                            self.failed_lines.append((line_num, line.strip()[:100]))

                    # Progress indicator for large files
                    if line_count % 10000 == 0:
                        print(f"  Processed {line_count:,} lines...", end='\r')

            print(f"✓ Successfully processed {parsed_count:,} out of {line_count:,} lines")

            if self.failed_lines:
                print(f"⚠ Warning: {line_count - parsed_count:,} lines could not be parsed")

        except Exception as e:
            print(f"✗ Error processing file: {e}", file=sys.stderr)
            raise

    def _update_statistics(self, parsed: Dict) -> None:
        """Update statistics with parsed log entry."""
        self.total_requests += 1

        ip = parsed.get('ip', 'unknown')
        method = parsed.get('method', 'unknown')
        endpoint = parsed.get('endpoint', 'unknown')
        status = parsed.get('status', '000')

        # Update counters
        self.ip_requests[ip] += 1
        self.endpoints[endpoint] += 1
        self.status_codes[status] += 1
        self.methods[method] += 1

        # Track errors (4xx and 5xx status codes)
        if status.startswith('4') or status.startswith('5'):
            self.ip_errors[ip] += 1

    def identify_suspicious_ips(self) -> List[Tuple[str, int, int, float]]:
        """
        Identify suspicious IPs based on error rates.

        Returns:
            List of tuples: (ip, total_requests, errors, error_rate)
        """
        suspicious = []

        for ip, total in self.ip_requests.items():
            errors = self.ip_errors.get(ip, 0)
            error_rate = errors / total if total > 0 else 0

            if errors >= self.error_threshold and error_rate >= self.error_rate_threshold:
                suspicious.append((ip, total, errors, error_rate))

        # Sort by error count descending
        suspicious.sort(key=lambda x: x[2], reverse=True)
        return suspicious

    def generate_statistics(self) -> Dict:
        """
        Generate comprehensive statistics report.

        Returns:
            Dictionary containing all statistics
        """
        suspicious_ips = self.identify_suspicious_ips()

        return {
            'summary': {
                'total_requests': self.total_requests,
                'unique_ips': len(self.ip_requests),
                'unique_endpoints': len(self.endpoints),
                'unique_status_codes': len(self.status_codes),
                'suspicious_ips_count': len(suspicious_ips)
            },
            'http_methods': dict(self.methods.most_common()),
            'status_codes': {
                'breakdown': dict(self.status_codes.most_common()),
                'summary': {
                    '2xx_success': sum(count for code, count in self.status_codes.items() if code.startswith('2')),
                    '3xx_redirect': sum(count for code, count in self.status_codes.items() if code.startswith('3')),
                    '4xx_client_error': sum(count for code, count in self.status_codes.items() if code.startswith('4')),
                    '5xx_server_error': sum(count for code, count in self.status_codes.items() if code.startswith('5'))
                }
            },
            'top_endpoints': [
                {'endpoint': endpoint, 'requests': count}
                for endpoint, count in self.endpoints.most_common(20)
            ],
            'top_ips': [
                {'ip': ip, 'requests': count}
                for ip, count in Counter(self.ip_requests).most_common(20)
            ],
            'suspicious_ips': [
                {
                    'ip': ip,
                    'total_requests': total,
                    'errors': errors,
                    'error_rate': round(error_rate, 3)
                }
                for ip, total, errors, error_rate in suspicious_ips
            ]
        }

    def display_console_report(self) -> None:
        """Display formatted statistics in the console."""
        stats = self.generate_statistics()

        print(f"\n{'=' * 80}")
        print("📊 WEB SERVER LOG ANALYSIS REPORT")
        print(f"{'=' * 80}\n")

        # Summary
        print("📈 SUMMARY")
        print(f"{'─' * 80}")
        summary = stats['summary']
        print(f"  Total Requests:        {summary['total_requests']:>15,}")
        print(f"  Unique IPs:            {summary['unique_ips']:>15,}")
        print(f"  Unique Endpoints:      {summary['unique_endpoints']:>15,}")
        print(f"  Suspicious IPs:        {summary['suspicious_ips_count']:>15,}")

        # HTTP Methods
        print(f"\n🔧 HTTP METHODS")
        print(f"{'─' * 80}")
        for method, count in sorted(stats['http_methods'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / summary['total_requests']) * 100
            print(f"  {method:<10} {count:>10,} ({percentage:>5.1f}%)")

        # Status Codes Summary
        print(f"\n📡 STATUS CODE SUMMARY")
        print(f"{'─' * 80}")
        status_summary = stats['status_codes']['summary']
        for category, count in status_summary.items():
            if count > 0:
                percentage = (count / summary['total_requests']) * 100
                print(f"  {category:<20} {count:>10,} ({percentage:>5.1f}%)")

        # Detailed Status Codes
        print(f"\n📡 STATUS CODE BREAKDOWN (Top 10)")
        print(f"{'─' * 80}")
        for code, count in list(stats['status_codes']['breakdown'].items())[:10]:
            percentage = (count / summary['total_requests']) * 100
            status_name = self._get_status_name(code)
            print(f"  {code} {status_name:<30} {count:>10,} ({percentage:>5.1f}%)")

        # Top Endpoints
        print(f"\n🎯 TOP ENDPOINTS (Top 15)")
        print(f"{'─' * 80}")
        for i, item in enumerate(stats['top_endpoints'][:15], 1):
            endpoint = item['endpoint']
            count = item['requests']
            percentage = (count / summary['total_requests']) * 100
            # Truncate long endpoints
            if len(endpoint) > 50:
                endpoint = endpoint[:47] + '...'
            print(f"  {i:>2}. {endpoint:<50} {count:>8,} ({percentage:>5.1f}%)")

        # Top IPs
        print(f"\n🌐 TOP IP ADDRESSES (Top 15)")
        print(f"{'─' * 80}")
        for i, item in enumerate(stats['top_ips'][:15], 1):
            ip = item['ip']
            count = item['requests']
            percentage = (count / summary['total_requests']) * 100
            print(f"  {i:>2}. {ip:<15} {count:>10,} ({percentage:>5.1f}%)")

        # Suspicious IPs
        if stats['suspicious_ips']:
            print(f"\n⚠️  SUSPICIOUS IP ADDRESSES")
            print(f"{'─' * 80}")
            print(f"  {'IP Address':<15} {'Requests':>10} {'Errors':>10} {'Error Rate':>12}")
            print(f"  {'-' * 15} {'-' * 10} {'-' * 10} {'-' * 12}")
            for item in stats['suspicious_ips'][:20]:
                print(f"  {item['ip']:<15} {item['total_requests']:>10,} "
                      f"{item['errors']:>10,} {item['error_rate']:>11.1%}")

        # Parsing warnings
        if self.failed_lines:
            print(f"\n⚠️  PARSING WARNINGS")
            print(f"{'─' * 80}")
            print(f"  {len(self.failed_lines)} sample lines could not be parsed:")
            for line_num, line in self.failed_lines[:5]:
                print(f"  Line {line_num}: {line}")

        print(f"\n{'=' * 80}\n")

    def _get_status_name(self, code: str) -> str:
        """Get human-readable status code name."""
        status_names = {
            '200': 'OK',
            '201': 'Created',
            '204': 'No Content',
            '301': 'Moved Permanently',
            '302': 'Found',
            '304': 'Not Modified',
            '400': 'Bad Request',
            '401': 'Unauthorized',
            '403': 'Forbidden',
            '404': 'Not Found',
            '405': 'Method Not Allowed',
            '500': 'Internal Server Error',
            '502': 'Bad Gateway',
            '503': 'Service Unavailable',
            '504': 'Gateway Timeout'
        }
        return status_names.get(code, '')

    def save_json_report(self, output_path: str) -> None:
        """
        Save detailed report to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        stats = self.generate_statistics()

        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analyzer_version': '1.0.0',
                'error_threshold': self.error_threshold,
                'error_rate_threshold': self.error_rate_threshold
            },
            'statistics': stats
        }

        output_path = Path(output_path)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"💾 Report saved to: {output_path.absolute()}")
            print(f"   File size: {output_path.stat().st_size:,} bytes")

        except Exception as e:
            print(f"✗ Error saving report: {e}", file=sys.stderr)
            raise


def main():
    """Main entry point for the log analyzer."""
    parser = argparse.ArgumentParser(
        description='Analyze web server log files (Apache/Nginx) and generate statistics reports.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single log file
  python log_analyzer.py access.log

  # Analyze with custom output file
  python log_analyzer.py access.log -o report.json

  # Analyze with custom thresholds
  python log_analyzer.py access.log --error-threshold 20 --error-rate 0.3

  # Skip console output, only generate JSON
  python log_analyzer.py access.log --json-only
        """
    )

    parser.add_argument(
        'logfile',
        help='Path to the log file to analyze'
    )

    parser.add_argument(
        '-o', '--output',
        default='log_report.json',
        help='Output JSON report file (default: log_report.json)'
    )

    parser.add_argument(
        '--error-threshold',
        type=int,
        default=10,
        help='Minimum number of errors to flag an IP as suspicious (default: 10)'
    )

    parser.add_argument(
        '--error-rate',
        type=float,
        default=0.5,
        help='Minimum error rate (0-1) to flag an IP as suspicious (default: 0.5)'
    )

    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Skip console output, only generate JSON report'
    )

    args = parser.parse_args()

    # Validate arguments
    if not 0 <= args.error_rate <= 1:
        parser.error("Error rate must be between 0 and 1")

    try:
        # Create analyzer
        analyzer = LogAnalyzer(
            error_threshold=args.error_threshold,
            error_rate_threshold=args.error_rate
        )

        # Process log file
        analyzer.process_log_file(args.logfile)

        # Display console report
        if not args.json_only:
            analyzer.display_console_report()

        # Save JSON report
        analyzer.save_json_report(args.output)

        print("\n✓ Analysis completed successfully!")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Analysis interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
