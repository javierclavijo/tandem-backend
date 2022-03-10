# Generated by Django 4.0.2 on 2022-03-10 09:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=2048)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ChannelChatMessageCorrection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('EN', 'English'), ('ES', 'Spanish'), ('FR', 'French'), ('DE', 'German'), ('IT', 'Italian')], max_length=2)),
                ('corrected_content', models.TextField(max_length=4096)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChannelChatMessageTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('EN', 'English'), ('ES', 'Spanish'), ('FR', 'French'), ('DE', 'German'), ('IT', 'Italian')], max_length=2)),
                ('translated_content', models.TextField(max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='UserChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='UserChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=2048)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='UserChatMessageTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('EN', 'English'), ('ES', 'Spanish'), ('FR', 'French'), ('DE', 'German'), ('IT', 'Italian')], max_length=2)),
                ('translated_content', models.TextField(max_length=4096)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='chats.userchatmessage')),
            ],
        ),
        migrations.CreateModel(
            name='UserChatMessageCorrection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='correction', to='chats.userchatmessage')),
            ],
        ),
    ]
