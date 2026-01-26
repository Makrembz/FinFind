"""
Upload and Verify Script for FinFind.

This script provides a complete workflow for uploading all generated
synthetic data to Qdrant Cloud and verifying the upload was successful.
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def run_upload(input_dir: Path, recreate: bool = False):
    """Run the data upload process."""
    from uploaders.qdrant_uploader import QdrantUploader, UploadConfig
    
    config = UploadConfig(input_dir=input_dir)
    uploader = QdrantUploader(config)
    
    if recreate:
        logger.info("Recreating all collections...")
        uploader.create_all_collections(recreate=True)
    
    logger.info("Starting upload process...")
    results = uploader.upload_all()
    
    return results


def run_verification(
    expected_products: int = 500,
    expected_users: int = 100,
    expected_reviews: int = 1200,
    expected_interactions: int = 2000
):
    """Run the data verification process."""
    from uploaders.verify_upload import QdrantVerifier, VerificationConfig
    
    config = VerificationConfig(
        expected_products=expected_products,
        expected_users=expected_users,
        expected_reviews=expected_reviews,
        expected_interactions=expected_interactions
    )
    
    verifier = QdrantVerifier(config)
    passed, failed = verifier.run_all_verifications()
    all_passed = verifier.print_report()
    
    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Upload and verify FinFind data in Qdrant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full upload and verification
  python upload_and_verify.py --all
  
  # Upload only
  python upload_and_verify.py --upload
  
  # Verify only
  python upload_and_verify.py --verify
  
  # Upload with fresh collections (delete existing)
  python upload_and_verify.py --upload --recreate
  
  # Specify custom input directory
  python upload_and_verify.py --all --input-dir ./my_data
        """
    )
    
    # Main mode options
    mode_group = parser.add_argument_group('Mode')
    mode_group.add_argument(
        '--all',
        action='store_true',
        help='Run both upload and verification'
    )
    mode_group.add_argument(
        '--upload',
        action='store_true',
        help='Run upload only'
    )
    mode_group.add_argument(
        '--verify',
        action='store_true',
        help='Run verification only'
    )
    
    # Upload options
    upload_group = parser.add_argument_group('Upload Options')
    upload_group.add_argument(
        '--input-dir',
        type=str,
        default='output',
        help='Input directory containing JSON files (default: output)'
    )
    upload_group.add_argument(
        '--recreate',
        action='store_true',
        help='Delete and recreate collections before upload'
    )
    
    # Verification options
    verify_group = parser.add_argument_group('Verification Options')
    verify_group.add_argument(
        '--expected-products',
        type=int,
        default=500,
        help='Expected number of products (default: 500)'
    )
    verify_group.add_argument(
        '--expected-users',
        type=int,
        default=100,
        help='Expected number of users (default: 100)'
    )
    verify_group.add_argument(
        '--expected-reviews',
        type=int,
        default=1200,
        help='Expected number of reviews (default: 1200)'
    )
    verify_group.add_argument(
        '--expected-interactions',
        type=int,
        default=2000,
        help='Expected number of interactions (default: 2000)'
    )
    
    # Logging options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Validate mode
    if not any([args.all, args.upload, args.verify]):
        parser.print_help()
        print("\nError: Please specify --all, --upload, or --verify")
        return 1
    
    start_time = datetime.now()
    input_dir = Path(args.input_dir)
    
    print("\n" + "=" * 70)
    print("           FINFIND QDRANT UPLOAD AND VERIFICATION")
    print("=" * 70)
    print(f"\nStarted at: {start_time.isoformat()}")
    print(f"Input directory: {input_dir.absolute()}")
    print(f"Mode: {'Upload + Verify' if args.all else 'Upload' if args.upload else 'Verify'}")
    print("-" * 70)
    
    success = True
    
    # Run upload
    if args.all or args.upload:
        print("\n📤 UPLOAD PHASE")
        print("-" * 40)
        
        try:
            results = run_upload(input_dir, args.recreate)
            
            # Check results
            upload_success = all(r['success'] for r in results.values())
            total_points = sum(r.get('points_uploaded', 0) for r in results.values())
            
            print(f"\nUpload complete: {total_points} total points")
            
            for collection, result in results.items():
                status = "✓" if result['success'] else "✗"
                count = result.get('points_uploaded', 0)
                print(f"  {status} {collection}: {count} points")
            
            if not upload_success:
                success = False
                
        except Exception as e:
            logger.exception(f"Upload failed: {e}")
            success = False
    
    # Run verification
    if (args.all or args.verify) and success:
        print("\n🔍 VERIFICATION PHASE")
        print("-" * 40)
        
        try:
            all_passed = run_verification(
                expected_products=args.expected_products,
                expected_users=args.expected_users,
                expected_reviews=args.expected_reviews,
                expected_interactions=args.expected_interactions
            )
            
            if not all_passed:
                success = False
                
        except Exception as e:
            logger.exception(f"Verification failed: {e}")
            success = False
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Duration: {duration}")
    print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 70 + "\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
