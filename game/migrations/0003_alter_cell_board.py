# Generated by Django 4.0.6 on 2024-06-27 16:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_alter_board_success'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cell',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cells', to='game.board'),
        ),
    ]
