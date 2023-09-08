import supabase


class SupabaseHandler:

    def __init__(self, supabase_url, supabase_key):
        self.__client = supabase.Client(supabase_url, supabase_key)

    def sign_in_with_password(self, user_credentials: dict):
        return self.__client.auth.sign_in_with_password(user_credentials)

    async def get_user_by_id(self, userid):
        data = self.__client.table('Users').select('*').eq('id', str(userid)).execute()
        print(data.data)
        return data
