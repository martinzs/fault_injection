#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>

int main(int argc, char *args[])
{
    FILE *f;
    for (int i = 0; i < 10; i++)
    {
        f = fopen(args[1], "r");
        if (f == NULL)
        {
            perror("ERROR: ");
        }
        else
            fclose(f);
        sleep(3);
    }
}
