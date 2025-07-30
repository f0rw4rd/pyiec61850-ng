#!/usr/bin/env python3
"""
Run all tests for pyiec61850
"""

import sys
import os
import unittest
import argparse


def run_tests(verbosity=2, pattern='test*.py'):
    """Run all tests in the tests directory"""
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(description='Run pyiec61850 tests')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Minimal output')
    parser.add_argument('-p', '--pattern', default='test*.py',
                        help='Test file pattern (default: test*.py)')
    parser.add_argument('--skip-connection-tests', action='store_true',
                        help='Skip tests that require a connection to a server')
    
    args = parser.parse_args()
    
    # Set environment variable for skipping connection tests
    if args.skip_connection_tests:
        os.environ['SKIP_CONNECTION_TESTS'] = 'true'
    
    # Determine verbosity level
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    # Run tests
    exit_code = run_tests(verbosity=verbosity, pattern=args.pattern)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()