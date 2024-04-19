class StringUtils:
    def limit(input_str, max_length):
        if input_str is None:
            raise ValueError("input_str cannot be None")
        if max_length <= 0:
            raise ValueError("max_length must be greater than zero")
        if len(input_str) <= max_length:
            return input_str
        return input_str[:max_length - 3].strip() + "..."

class IntUtils:
    def humanize_number(number):
        num_suffixes = ["", "K", "M", "B", "T"]
        magnitude = 0
        if not isinstance(number, float):
            number = float(number)
        while abs(number) >= 1000 and magnitude < len(num_suffixes) - 1:
            magnitude += 1
            number /= 1000.0
        formatted_number = "{:.2f}{}".format(number, num_suffixes[magnitude]) if num_suffixes[magnitude] else "{:.0f}".format(number)
        return formatted_number