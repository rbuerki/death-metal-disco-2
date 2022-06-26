from discobase.models import RecordFormat, Genre

genre_dict = {g.pk: g.genre_name for g in Genre.objects.all()}
genre_choices = sorted(genre_dict.items(), key=lambda x: x[1], reverse=False)
format_dict = {f.pk: f.format_name for f in RecordFormat.objects.all()}
format_choices = sorted(format_dict.items(), key=lambda x: x[1], reverse=False)
rating_dict = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
rating_choices = sorted(rating_dict.items(), key=lambda x: x[1], reverse=False)
