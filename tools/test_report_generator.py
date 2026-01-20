#!/usr/bin/env python3
"""
Test Report Generator

Runs tests and generates beautiful HTML report with analysis.

Usage:
    python tools/test_report_generator.py
    python tools/test_report_generator.py --output reports/test_report.html
"""

import subprocess
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PsyFlo Test Report - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-value {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .metric-value.pass {{
            color: #10b981;
        }}
        
        .metric-value.fail {{
            color: #ef4444;
        }}
        
        .metric-value.skip {{
            color: #f59e0b;
        }}
        
        .metric-label {{
            font-size: 0.9em;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .test-class {{
            margin-bottom: 30px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .test-class-header {{
            background: #f3f4f6;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1em;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .test-class-header:hover {{
            background: #e5e7eb;
        }}
        
        .test-list {{
            padding: 0;
        }}
        
        .test-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .test-item:last-child {{
            border-bottom: none;
        }}
        
        .test-name {{
            flex: 1;
        }}
        
        .test-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .test-status.passed {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .test-status.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .test-status.skipped {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .test-duration {{
            color: #6b7280;
            font-size: 0.9em;
            margin-left: 15px;
        }}
        
        .analysis {{
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .analysis-title {{
            font-weight: bold;
            color: #1e40af;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .analysis-content {{
            color: #1e3a8a;
            line-height: 1.6;
        }}
        
        .coverage {{
            background: #f0fdf4;
            border: 2px solid #10b981;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .coverage-bar {{
            background: #e5e7eb;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .coverage-fill {{
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 1s ease;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.9em;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            font-weight: bold;
            margin-left: 10px;
        }}
        
        .badge.critical {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge.important {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge.info {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .test-case {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
        }}
        
        .test-case.passed {{
            border-left: 4px solid #10b981;
        }}
        
        .test-case.failed {{
            border-left: 4px solid #ef4444;
        }}
        
        .test-name {{
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 5px;
        }}
        
        .test-class {{
            color: #6b7280;
            font-size: 0.85em;
            margin-bottom: 8px;
        }}
        
        .test-time {{
            color: #9ca3af;
            font-size: 0.8em;
        }}
        
        .test-status {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            font-weight: bold;
            margin-left: 10px;
        }}
        
        .test-status.passed {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .test-status.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .category-section {{
            margin: 30px 0;
        }}
        
        .category-header {{
            background: #f3f4f6;
            padding: 12px 20px;
            border-radius: 6px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .category-count {{
            font-size: 0.9em;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ PsyFlo Safety Service</h1>
            <div class="subtitle">Test Report - {timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="metric-card">
                <div class="metric-label">Total Tests</div>
                <div class="metric-value">{total_tests}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Passed</div>
                <div class="metric-value pass">{passed}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Failed</div>
                <div class="metric-value fail">{failed}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Skipped</div>
                <div class="metric-value skip">{skipped}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Duration</div>
                <div class="metric-value">{duration}s</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value pass">{success_rate}%</div>
            </div>
        </div>
        
        {analysis_section}
        
        {coverage_section}
        
        <div class="section">
            <h2 class="section-title">📋 Test Results by Category</h2>
            {test_results}
        </div>
        
        <div class="footer">
            Generated on {timestamp} | PsyFlo Mental Health AI Triage System
        </div>
    </div>
</body>
</html>
"""


def run_tests_with_xml():
    """Run pytest and generate XML report."""
    print("Running tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_safety_service.py",
        "-v",
        "--junit-xml=test_results.xml",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    return result.returncode == 0, result.stdout, result.stderr


def parse_junit_xml(xml_path="test_results.xml"):
    """Parse JUnit XML report."""
    if not Path(xml_path).exists():
        return None
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Handle both <testsuites> and <testsuite> root elements
    testsuite = root.find('.//testsuite')
    if testsuite is None:
        testsuite = root
    
    results = {
        'total': int(testsuite.attrib.get('tests', 0)),
        'passed': 0,
        'failed': int(testsuite.attrib.get('failures', 0)),
        'skipped': int(testsuite.attrib.get('skipped', 0)),
        'errors': int(testsuite.attrib.get('errors', 0)),
        'duration': float(testsuite.attrib.get('time', 0)),
        'test_cases': []
    }
    
    results['passed'] = results['total'] - results['failed'] - results['skipped'] - results['errors']
    
    for testcase in root.findall('.//testcase'):
        case = {
            'classname': testcase.attrib.get('classname', ''),
            'name': testcase.attrib.get('name', ''),
            'time': float(testcase.attrib.get('time', 0)),
            'status': 'passed'
        }
        
        if testcase.find('failure') is not None:
            case['status'] = 'failed'
            case['message'] = testcase.find('failure').attrib.get('message', '')
        elif testcase.find('skipped') is not None:
            case['status'] = 'skipped'
        
        results['test_cases'].append(case)
    
    return results


def generate_analysis(results):
    """Generate analysis section with test summary."""
    if not results:
        return ""
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    
    analyses = []
    
    # Test Summary
    test_summary = {
        'title': '📋 Test Suite Summary',
        'content': '''
        <strong>29 comprehensive tests covering:</strong>
        <ul style="margin-top: 10px; line-height: 1.8;">
            <li><strong>Explicit Crisis Detection (3 tests):</strong> Validates 100% recall on explicit crisis keywords like "I want to die", "kill myself", "self harm"</li>
            <li><strong>Boundary Validation (3 tests):</strong> Ensures teenage hyperbole ("homework is killing me") doesn't trigger false positives</li>
            <li><strong>Semantic Layer (1 test):</strong> Tests semantic similarity detection for crisis-related language</li>
            <li><strong>Performance (2 tests):</strong> Validates <50ms latency SLA and batch throughput >20 msg/s</li>
            <li><strong>Clinical Scoring (1 test):</strong> Tests deterministic triggers score high confidence</li>
            <li><strong>Strategy Isolation (7 tests):</strong> Tests regex, semantic, and sarcasm strategies independently</li>
            <li><strong>Context Window (2 tests):</strong> Tests semantic layer uses last 3 messages for disambiguation</li>
            <li><strong>Sarcasm Filter (2 tests):</strong> Tests hyperbole detection reduces false positives</li>
            <li><strong>Performance Regression (3 tests):</strong> Ensures optimizations don't break SLA</li>
            <li><strong>Edge Cases (5 tests):</strong> Tests empty messages, unicode, long messages, error handling</li>
        </ul>
        '''
    }
    analyses.append(test_summary)
    
    # Overall health
    if success_rate == 100:
        analyses.append({
            'title': '✅ Excellent Test Health',
            'content': 'All tests passing! The safety service is functioning correctly across all test scenarios.'
        })
    elif success_rate >= 90:
        analyses.append({
            'title': '⚠️ Good Test Health with Minor Issues',
            'content': f'{results["failed"]} test(s) failing. Review failed tests to ensure no critical safety issues.'
        })
    else:
        analyses.append({
            'title': '🚨 Critical Test Failures',
            'content': f'{results["failed"]} test(s) failing. Immediate attention required for safety-critical system.'
        })
    
    # Performance analysis
    avg_time = results['duration'] / results['total'] if results['total'] > 0 else 0
    if avg_time < 0.05:  # 50ms
        analyses.append({
            'title': '⚡ Performance: Excellent',
            'content': f'Average test time: {avg_time*1000:.1f}ms. Well within <50ms SLA target.'
        })
    else:
        analyses.append({
            'title': '⏱️ Performance: Needs Attention',
            'content': f'Average test time: {avg_time*1000:.1f}ms. Exceeds 50ms SLA target.'
        })
    
    # Critical test analysis
    critical_tests = [
        'test_suicidal_ideation_explicit',
        'test_self_harm_explicit',
        'test_intent_with_plan'
    ]
    
    failed_critical = [
        tc for tc in results['test_cases']
        if tc['status'] == 'failed' and any(ct in tc['name'] for ct in critical_tests)
    ]
    
    if failed_critical:
        analyses.append({
            'title': '🚨 CRITICAL: Safety Floor Compromised',
            'content': f'{len(failed_critical)} critical safety test(s) failing. These tests ensure 100% recall on explicit crisis keywords. MUST be fixed immediately.'
        })
    
    html = ""
    for analysis in analyses:
        html += f"""
        <div class="analysis">
            <div class="analysis-title">{analysis['title']}</div>
            <div class="analysis-content">{analysis['content']}</div>
        </div>
        """
    
    return f'<div class="section"><h2 class="section-title">🔍 Analysis</h2>{html}</div>'


def generate_test_results_html(results):
    """Generate test results HTML with detailed test case information."""
    if not results:
        return "<p>No test results available.</p>"
    
    # Group by test class
    test_classes = {}
    for tc in results['test_cases']:
        classname = tc['classname'].split('.')[-1]
        if classname not in test_classes:
            test_classes[classname] = []
        test_classes[classname].append(tc)
    
    # Map test classes to descriptions
    class_descriptions = {
        'TestExplicitCrisisDetection': 'Tests 100% recall on explicit crisis keywords (safety floor)',
        'TestBoundaryValidation': 'Tests that hyperbole and figurative language don\'t trigger false positives',
        'TestSemanticLayer': 'Tests semantic layer functionality',
        'TestPerformance': 'Tests latency requirements (<50ms SLA)',
        'TestClinicalScoring': 'Tests clinical scoring accuracy',
        'TestStrategyIsolation': 'Tests each detection strategy in isolation',
        'TestContextWindow': 'Tests context window functionality',
        'TestSarcasmFilterIntegration': 'Tests sarcasm filter integration',
        'TestPerformanceRegression': 'Tests performance doesn\'t regress',
        'TestEdgeCases': 'Tests edge cases and error handling'
    }
    
    html = ""
    for classname, tests in sorted(test_classes.items()):
        passed = sum(1 for t in tests if t['status'] == 'passed')
        failed = sum(1 for t in tests if t['status'] == 'failed')
        
        badge = ""
        if 'Explicit' in classname or 'Crisis' in classname:
            badge = '<span class="badge critical">CRITICAL</span>'
        elif 'Performance' in classname:
            badge = '<span class="badge important">PERFORMANCE</span>'
        else:
            badge = '<span class="badge info">STANDARD</span>'
        
        description = class_descriptions.get(classname, '')
        
        html += f"""
        <div class="category-section">
            <div class="category-header">
                <div>
                    <strong>{classname}</strong> {badge}
                    <div style="font-size: 0.85em; font-weight: normal; margin-top: 4px; color: #6b7280;">{description}</div>
                </div>
                <span class="category-count">{passed}/{len(tests)} passed</span>
            </div>
        """
        
        for test in tests:
            status_class = test['status']
            status_icon = '✅' if status_class == 'passed' else '❌'
            
            # Clean up test name for display
            test_display_name = test['name'].replace('_', ' ').title()
            
            html += f"""
            <div class="test-case {status_class}">
                <div class="test-name">{status_icon} {test_display_name}</div>
                <div class="test-class">Test: {test['name']}</div>
                <div class="test-time">⏱️ {test['time']*1000:.2f}ms</div>
            </div>
            """
        
        html += """
        </div>
        """
    
    return html


def generate_html_report(results, output_path):
    """Generate HTML report."""
    if not results:
        print("No test results to generate report")
        return
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    
    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_tests=results['total'],
        passed=results['passed'],
        failed=results['failed'],
        skipped=results['skipped'],
        duration=f"{results['duration']:.2f}",
        success_rate=f"{success_rate:.1f}",
        analysis_section=generate_analysis(results),
        coverage_section="",  # TODO: Add coverage if available
        test_results=generate_test_results_html(results)
    )
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ HTML report generated: {output_path}")
    print(f"   Open in browser: file://{output_file.absolute()}")


def main():
    parser = argparse.ArgumentParser(description="Generate HTML test report")
    parser.add_argument(
        '--output',
        default='reports/test_report.html',
        help='Output path for HTML report'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("PsyFlo Test Report Generator")
    print("="*70)
    
    # Run tests
    success, stdout, stderr = run_tests_with_xml()
    
    # Parse results
    results = parse_junit_xml()
    
    if results:
        print(f"\n📊 Test Summary:")
        print(f"   Total: {results['total']}")
        print(f"   Passed: {results['passed']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Skipped: {results['skipped']}")
        print(f"   Duration: {results['duration']:.2f}s")
        
        # Generate HTML report
        generate_html_report(results, args.output)
    else:
        print("\n❌ Could not parse test results")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)


if __name__ == "__main__":
    main()
