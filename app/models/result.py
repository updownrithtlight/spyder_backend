from flask import jsonify, make_response


class ResponseTemplate:
    @staticmethod
    def success(message='Success',data=None):
        """标准化成功返回，默认 message = 'Success'，默认 HTTP 状态码 200"""
        response = jsonify({
            'success': True,
            'data': data or {},
            'message': message
        })
        return make_response(response, 200)  # 直接返回 200

    @staticmethod
    def error(message='Error', status_code=400):
        """标准化错误返回，支持自定义 HTTP 状态码"""
        response = jsonify({
            'success': False,
            'data': None,
            'message': message
        })
        return make_response(response, status_code)


class ResponsePageTemplate:
    @staticmethod
    def success(data=None, total_pages=0, current_page=0):
        """分页成功返回，默认 message = 'Success'"""
        response = jsonify({
            'success': True,
            'data': data or {},
            'totalPages': total_pages,
            'currentPage': current_page,
            'message': 'Success'
        })
        return make_response(response, 200)

    @staticmethod
    def error(message='Error', status_code=400):
        """分页错误返回"""
        response = jsonify({
            'success': False,
            'data': None,
            'message': message
        })
        return make_response(response, status_code)
