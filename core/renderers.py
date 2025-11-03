from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer for consistent response format
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        
        if response and hasattr(response, 'status_code'):
            if response.status_code >= 400:
                # Error response
                custom_data = {
                    'success': False,
                    'error': data,
                    'data': None,
                }
            else:
                # Success response
                custom_data = {
                    'success': True,
                    'data': data,
                    'error': None,
                }
        else:
            custom_data = data
            
        return super().render(custom_data, accepted_media_type, renderer_context)
