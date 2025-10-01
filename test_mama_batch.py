import sys
sys.path.insert(0, '.')

from app import app
from models import Blog, AutomationRule
from utils.automation.workflow_engine import WorkflowEngine

def test_batch_for_blog(blog_name: str, num_articles: int):
    with app.app_context():
        blog = Blog.query.filter_by(name=blog_name).first()
        if not blog:
            print(f'❌ Blog {blog_name} not found!')
            return
        
        print(f'\n✅ Found blog: {blog.name} (ID: {blog.id})')
        
        rule = AutomationRule.query.filter_by(blog_id=blog.id, is_active=True).first()
        if not rule:
            print(f'❌ No active automation rule found!')
            return
        
        print(f'✅ Found automation rule: {rule.name}')
        print(f'\n🔄 Starting batch generation ({num_articles} articles)...')
        print('-' * 70)
        
        try:
            engine = WorkflowEngine()
            results = []
            
            for i in range(num_articles):
                print(f'\n📄 Generating article {i+1}/{num_articles}...')
                result = engine.execute_full_cycle(rule)
                results.append(result)
                
                if result.get('status') == 'completed':
                    print(f'   ✅ Article {i+1} completed successfully!')
                    if result.get('article_id'):
                        print(f'      Article ID: {result["article_id"]}')
                    if result.get('wordpress_post_id'):
                        print(f'      WordPress Post ID: {result["wordpress_post_id"]}')
                else:
                    print(f'   ❌ Article {i+1} failed!')
                    print(f'      Error: {result.get("error", "Unknown error")}')
            
            print('\n' + '='*70)
            print('📊 BATCH GENERATION RESULTS')
            print('='*70)
            print(f'Total articles: {len(results)}')
            successful = sum(1 for r in results if r.get('status') == 'completed')
            failed = len(results) - successful
            print(f'Successful: {successful}')
            print(f'Failed: {failed}')
            
        except Exception as e:
            print(f'\n❌ Error during batch generation: {e}')
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print('='*70)
    print('🚀 BATCH GENERATION TEST: MAMATESTUJE.COM')
    print('='*70)
    test_batch_for_blog('MAMATESTUJE.COM', 4)
