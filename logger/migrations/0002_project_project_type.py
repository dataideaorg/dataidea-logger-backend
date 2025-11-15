# Generated manually for adding project_type field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='project_type',
            field=models.CharField(
                choices=[('activity', 'Activity Event Logs'), ('llm', 'LLM Event Logs')],
                default='activity',
                help_text='Type of logs this project will handle',
                max_length=20
            ),
        ),
    ]