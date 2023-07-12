from vkbottle.bot import BotLabeler, rules

admin_labeler = BotLabeler()
admin_labeler.auto_rules = [rules.FromPeerRule(1)]


@admin_labeler.chat_message(text="halt")
async def halt(_):
    exit(0)
