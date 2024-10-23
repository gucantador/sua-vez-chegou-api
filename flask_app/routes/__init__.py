from flask import jsonify


class BaseResponse():

    def __init__(self, data, errors, message):
        self.data = data
        self.errors = errors
        self.message = message
        self.success = True if not self.errors else False

    def response(self):
        return jsonify(dict(data=self.data, errors=self.errors, message=self.message, success=self.success))


from . import costumer_routes